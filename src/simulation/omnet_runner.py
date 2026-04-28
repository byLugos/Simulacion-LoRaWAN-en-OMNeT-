import subprocess
import os

def run_simulation():
    # --- RUTAS ---
    opp_bin_dir = r"C:\omnetpp-6.0.3-windows-x86_64\omnetpp-6.0.3\bin"
    inet_bin_dir = r"C:\OmnetDos\inet4.4\out\clang-release\src"
    flora_bin_dir = r"C:\OmnetDos\flora-1.1.0\out\clang-release\src"

    project_root = os.path.dirname(os.getcwd())
    simulations_dir = os.path.join(project_root, "simulations")
    project_ned_dir = os.path.join(project_root, "src")
    ini_path = os.path.join(simulations_dir, "omnetpp.ini")

    # --- CONFIGURAR ENTORNO (PATH) ---
    env = os.environ.copy()
    # Añadimos TODAS las rutas necesarias al PATH para que las DLLs se encuentren entre sí
    additional_paths = [opp_bin_dir, inet_bin_dir, flora_bin_dir]
    env["PATH"] = ";".join(additional_paths) + ";" + env.get("PATH", "")

    # --- COMANDO ---
    opp_run_exe = os.path.join(opp_bin_dir, "opp_run.exe")

    opp_run_command = [
        opp_run_exe,
        "-m",
        "-u", "Qtenv",
        "-n", f"{simulations_dir};{project_ned_dir};C:/OmnetDos/inet4.4/src;C:/OmnetDos/flora-1.1.0/src",
        "--image-path", "C:/OmnetDos/inet4.4/images;C:/OmnetDos/flora-1.1.0/images",
        "-l", "INET",  # OMNeT buscará libINET.dll en el PATH
        "-l", "flora", # OMNeT buscará libflora.dll en el PATH
        ini_path
    ]

    try:
        print("Lanzando simulación...")
        subprocess.run(opp_run_command, check=True, cwd=simulations_dir, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Error en la simulación: {e}")

if __name__ == "__main__":
    run_simulation()