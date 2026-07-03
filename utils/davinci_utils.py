import os
import sys
import tkinter as tk
from tkinter import messagebox

def show_error(title, msg):
    print(f"[报错弹窗] {title}: {msg}")
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    messagebox.showwarning(title, msg)
    root.destroy()

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
                            target_start_frame = item.GetStart()
                            target_timeline = tl
                            break
                if found_clip: break
            if found_clip: break
        if found_clip: break
        
    if not found_clip:
        print("[API] 遍历了所有时间线，未发现包含该链接的 Marker。")
        return False
        
    current_tl = project.GetCurrentTimeline()
    if current_tl.GetUniqueId() != target_timeline.GetUniqueId():
        print(f"[API] 发现目标不在当前时间线，执行切线: '{current_tl.GetName()}' -> '{target_timeline.GetName()}'")
        project.SetCurrentTimeline(target_timeline)
    else:
        print("[API] 目标就在当前时间线，无需切换。")
        
    fps_setting = float(target_timeline.GetSetting('timelineFrameRate'))
    fps_int = int(round(fps_setting)) 
    h = int(target_start_frame / (fps_int * 3600))
    m = int((target_start_frame / (fps_int * 60)) % 60)
    s = int((target_start_frame / fps_int) % 60)
    f = int(target_start_frame % fps_int)
    timecode_str = f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"
    
    print(f"[API] 帧率参数: {fps_setting}, 目标起始绝对帧: {target_start_frame}")
    print(f"[API] 换算时间码为: {timecode_str}")
    print("[API] 执行播放头跳转指令。")
    target_timeline.SetCurrentTimecode(timecode_str)
    
    return True
