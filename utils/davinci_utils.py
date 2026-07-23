import os
import sys
import time
from utils.common import show_toast
from utils.logger import log_info, log_error


def show_error(title, msg):
    print(f"[报错弹窗] {title}: {msg}")
    show_toast(msg, title=title, level="error")


def get_resolve():
    print("[API] 尝试连接 DaVinci Resolve Scripting 环境...")
    try:
        import DaVinciResolveScript as bmd
        print("[API] 原生环境连接成功。")
        return bmd.scriptapp("Resolve")
    except ImportError:
        expectedPath = os.getenv("RESOLVE_SCRIPT_API")
        if not expectedPath:
            expectedPath = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
        try:
            sys.path.append(expectedPath)
            import DaVinciResolveScript as bmd
            print("[API] 通过环境变量/绝对路径加载外部模块成功。")
            return bmd.scriptapp("Resolve")
        except Exception as e:
            print(f"[API] 外部连接彻底失败: {e}")
            return None

def find_clip_by_marker_name(target_url):
    resolve = get_resolve()
    if not resolve:
        show_error("错误", "无法连接到达芬奇 API，请确保达芬奇软件正在运行。")
        return False
        
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        show_error("错误", "达芬奇当前没有打开任何项目。")
        return False
        
    found_clip = None
    target_start_frame = None
    target_timeline = None

    timeline_count = project.GetTimelineCount()
    print(f"[API] 当前项目: '{project.GetName()}', 共有 {timeline_count} 个时间线。准备进行深度检索...")
    
    for tl_index in range(1, timeline_count + 1):
        tl = project.GetTimelineByIndex(tl_index)
        if not tl: continue
        
        track_count = tl.GetTrackCount('video')
        # 如果你想看更详细的每条时间线扫描过程，可以解开下面这行的注释
        # print(f"  -> 正在扫描时间线 [{tl.GetName()}] (包含 {track_count} 个视频轨)")
        
        for v_index in range(1, track_count + 1):
            items = tl.GetItemListInTrack('video', v_index)
            if not items: continue
            
            for item in items:
                markers = item.GetMarkers()
                if markers:
                    for frameId, marker_info in markers.items():
                        name = marker_info.get('name', '')
                        if target_url in name:
                            print(f"[API命中] 找到匹配的 Marker！")
                            print(f"       时间线: {tl.GetName()}")
                            print(f"       轨道: V{v_index}")
                            print(f"       片段名称: {item.GetName()}")
                            print(f"       Marker 标题: {name}")
                            found_clip = item
                            # 换算公式：片段在时间线的起始帧 + (Marker的源素材帧 - 片段在源素材的起始帧)
                            target_start_frame = item.GetStart() + (frameId - item.GetLeftOffset())
                            target_timeline = tl
                            break
                if found_clip: break
            if found_clip: break
        if found_clip: break
        
    if not found_clip:
        print("[API] 遍历了所有时间线，未发现包含该链接的 Marker。")
        return False
        
    current_tl = project.GetCurrentTimeline()
    target_id = target_timeline.GetUniqueId()

    if current_tl and current_tl.GetUniqueId() != target_id:
        log_info(f"[API] 发现目标不在当前时间线，执行切线: '{current_tl.GetName()}' -> '{target_timeline.GetName()}'")
        project.SetCurrentTimeline(target_timeline)

        # 核心改进：主动轮询校验 API，确保达芬奇完成时间线加载后再进行 SetCurrentTimecode
        retry_count = 0
        while retry_count < 20:
            active_tl = project.GetCurrentTimeline()
            if active_tl and active_tl.GetUniqueId() == target_id:
                log_info(f"[API] 确认时间线已真实切入并就绪！耗时约: {retry_count * 10}ms")
                break
            time.sleep(0.01)
            retry_count += 1
    else:
        log_info("[API] 目标就在当前时间线，无需切换。")

    # 在已确认就绪的时间线上执行 SetCurrentTimecode
    active_tl = project.GetCurrentTimeline() or target_timeline

    fps_setting = float(active_tl.GetSetting('timelineFrameRate'))
    fps_int = int(round(fps_setting))
    h = int(target_start_frame / (fps_int * 3600))
    m = int((target_start_frame / (fps_int * 60)) % 60)
    s = int((target_start_frame / fps_int) % 60)
    f = int(target_start_frame % fps_int)
    timecode_str = f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

    log_info(f"[API] 帧率参数: {fps_setting}, 目标起始绝对帧: {target_start_frame}")
    log_info(f"[API] 换算时间码为: {timecode_str}")
    log_info("[API] 执行播放头跳转指令。")
    active_tl.SetCurrentTimecode(timecode_str)

    # 双重兜底：主动校验播放头是否已真实飞跃至目标 timecode
    tc_retry = 0
    while tc_retry < 15:
        actual_tc = active_tl.GetCurrentTimecode()
        if actual_tc == timecode_str:
            log_info(f"[API] 确认播放头已精准跳转至目标时间码: {timecode_str} (校验耗时约: {tc_retry * 10}ms)")
            break
        time.sleep(0.01)
        active_tl.SetCurrentTimecode(timecode_str)
        tc_retry += 1
    else:
        log_info(f"[API] 提示：播放头跳转完成，当前实际时间码为: {active_tl.GetCurrentTimecode()}")

    return True


