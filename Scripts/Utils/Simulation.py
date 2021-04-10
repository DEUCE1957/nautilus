from datetime import datetime
from pathlib import Path
import psutil as ps, GPUtil as gp, time, numpy as np
from scipy.stats import mode
import multiprocessing
from subprocess import PIPE, DEVNULL, Popen, TimeoutExpired
from shutil import copytree
from .Enum import Color as C, CommonDirs

def format_bytes(bytes, unit, SI=False):
    """
    Converts bytes to common units such as kb, kib, KB, mb, mib, MB
    bytes (int) : Number of bytes to be converted
    unit (str) : Desired unit of measure for output
    SI (bool)
        True -> Use SI standard e.g. KB = 1000 bytes
        False -> Use JEDEC standard e.g. KB = 1024 bytes
    Returns (str) : Value WITHOUT unit
    """
    if unit.lower() in "b bit bits".split():
        return f"{bytes*8} {unit}"
    unitN = unit[0].upper()+unit[1:].replace("s","")  # Normalised
    reference = {"Kb Kib Kibibit Kilobit": (7, 1),
                 "KB KiB Kibibyte Kilobyte": (10, 1),
                 "Mb Mib Mebibit Megabit": (17, 2),
                 "MB MiB Mebibyte Megabyte": (20, 2),
                 "Gb Gib Gibibit Gigabit": (27, 3),
                 "GB GiB Gibibyte Gigabyte": (30, 3),
                 "Tb Tib Tebibit Terabit": (37, 4),
                 "TB TiB Tebibyte Terabyte": (40, 4),
                 "Pb Pib Pebibit Petabit": (47, 5),
                 "PB PiB Pebibyte Petabyte": (50, 5),
                 "Eb Eib Exbibit Exabit": (57, 6),
                 "EB EiB Exbibyte Exabyte": (60, 6),
                 "Zb Zib Zebibit Zettabit": (67, 7),
                 "ZB ZiB Zebibyte Zettabyte": (70, 7),
                 "Yb Yib Yobibit Yottabit": (77, 8),
                 "YB YiB Yobibyte Yottabyte": (80, 8),
                 }
    key_list = '\n'.join(["     b Bit"] + [x for x in reference.keys()]) +"\n"
    if unitN not in key_list:
        raise IndexError(f"\n\nConversion unit must be one of:\n\n{key_list}")
    units, divisors = [(k,v) for k,v in reference.items() if unitN in k][0]
    if SI:
        divisor = 1000**divisors[1]/8 if "bit" in units else 1000**divisors[1]
    else:
        divisor = float(1 << divisors[0])
    value = bytes / divisor
    if value != 1 and len(unitN) > 3:
            unitN += "s" # Create plural unit of measure
    return f"{value:.0f}"

def monitor_process(os, identifier, batch):
    while (dualSPH := get_dualsph_proc(os)) is None: 
        time.sleep(1)
    dualSPH.cpu_percent()  # Reference for future CPU measurements   
    res_path = CommonDirs.LOGS / f"{identifier.split('-')[1]}-{identifier.split('-')[0]}-RESOURCE_LOG.csv"
    try:
        while dualSPH.is_running():
            if dualSPH.status() == ps.STATUS_ZOMBIE:
                print(f"{C.YELLOW}{C.BOLD}WARNING{C.END}::MainProcess or DualSPHProcess Status = Zombie")
                break
            time.sleep(10)
            cpu_info = get_cpu_stats(dualSPH)
            gpu_info = []
            for GPU in gp.getGPUs():
                gpu_info.append([GPU.load * 100.0, GPU.memoryUtil * 100.0, GPU.memoryUsed, GPU.memoryTotal, GPU.temperature])
            
            with open(res_path, "a+") as f:
                if res_path.stat().st_size == 0: # True if empty
                    f.write("Batch Number,RAM Usage(MB),Virtual Memory(MB),CPU (%),CPU (FLOPS)," +
                            "CPU Freq (Hz),CPU User Time (s),CPU System Time (s),No. Threads," + 
                            ",".join([f"GPU_{i} (%),GPU_{i} Memory (%),GPU_{i} Memory Used (MB)," + 
                                       f"GPU_{i} Memory Total (MB),GPU_{i} Temp (C)" for i in range(len(gpu_info))]) + 
                            "\n") # Header
                f.write(f"{batch}," + ",".join([f"{elt}" for elt in cpu_info]) + "," +
                        ",".join([",".join([f"{elt}" for elt in info]) for info in gpu_info]) + "\n")
    except ps.NoSuchProcess:
        print(f"{C.YELLOW}{C.BOLD}WARNING{C.END}::MainProcess or DualSPHProcess Stopped Running")    

def get_dualsph_proc(os):
    name = "DualSPHysics"
    for p in ps.process_iter(["name", "exe", "cmdline"]):
        if name in p.info["name"] or \
           (p.info["exe"] and name in Path(p.info["exe"]).name) or \
           (p.info["cmdline"] and name in p.info["cmdline"][0]):
            return p
    return None

def get_cpu_stats(p):
    with p.oneshot():
        cpu_mem = p.memory_info()
        cpu_threads = p.num_threads()
        cpu_usage = p.cpu_percent() / float(cpu_threads)
        cpu_freq = ps.cpu_freq().current * 10**6 # Hz
        cpu_flops = (cpu_usage / 100.0) * cpu_freq # Hz
        cpu_times = p.cpu_times()
    return [format_bytes(cpu_mem.rss, "MB"), format_bytes(cpu_mem.vms, "MB"), cpu_usage, cpu_flops,
            cpu_freq, cpu_times.user, cpu_times.system, cpu_threads]         

def run_simulation(case_def, case_name, identifier="Default", os="win64", 
                   export_vtk=False, batch=0, 
                   timestamp=datetime.now().strftime("%d_%m_%Y_%Hh_%Mm_%Ss"),
                   copy_measurements=True, verbose=True):
    batch_path = str(case_def.parent / (case_name + f"_{os}_GPU" + (".bat" if os == "win64" else ".sh")))
    start_time = datetime.now()
    if verbose:
        print(f"Running Batch script: {batch_path}")  
    MainProcess = ps.Popen([("" if os=="win64" else "sudo ") + batch_path, "1" if export_vtk else "0"], shell=False if os=="win64" else True, 
                stdin=PIPE,
                # stdout=DEVNULL, # Don't print output of Script
                cwd=str(case_def.parent))
    if Path(case_def.parent / f"{case_name}_out").exists():
        try:
            time.sleep(5)
            if os == "win64":
                stdout, stderr = MainProcess.communicate(input=b"1")
            else:
                MainProcess.stdin.write(b"1")
        except TimeoutExpired:
            pass
    monitor = multiprocessing.Process(name="ResourceMonitor", target=monitor_process,
                                      args=(os, identifier, batch))
    monitor.start()                                  
    if os != "win64":
        stdout, stderr = MainProcess.communicate(input=b"A") # Will print to stdout, input ensures program exits
    monitor.terminate()
    duration = datetime.now()-start_time
    if verbose:
        print(f"{C.GREEN}{C.BOLD}Simulation Complete{C.END} in {duration} (HH:MM:SS)")

    if copy_measurements:
        # >> Store MeasureTool output in this workspace <<
        copytree(case_def.parent / (case_name + "_out") / "measurements",
                 CommonDirs.MEASURES / identifier / f"{case_name}-{timestamp}-Batch{batch}")
    return duration