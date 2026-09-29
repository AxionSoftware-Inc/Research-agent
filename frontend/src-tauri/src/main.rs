// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

struct BackendManager {
    child: Mutex<Option<Child>>,
}

fn is_backend_running() -> bool {
    let addr = "127.0.0.1:8765".parse();
    if let Ok(sa) = addr {
        TcpStream::connect_timeout(&sa, Duration::from_millis(500)).is_ok()
    } else {
        false
    }
}

fn find_project_and_python() -> Option<(PathBuf, PathBuf, bool)> {
    // Returns (project_dir, executable_path, is_standalone_binary)
    if let Ok(mut current_dir) = std::env::current_exe() {
        current_dir.pop(); // remove binary name

        // 1. Check if agent-backend.exe exists in the same folder as the Tauri app
        let standalone = current_dir.join("agent-backend.exe");
        if standalone.is_file() {
            return Some((current_dir, standalone, true));
        }

        // 2. Search upwards for .venv and agent folder
        let mut search_dir: Option<&Path> = Some(&current_dir);
        for _ in 0..5 {
            if let Some(dir) = search_dir {
                let venv_py = dir.join(".venv").join("Scripts").join("python.exe");
                let agent_pkg = dir.join("agent");
                if venv_py.is_file() && agent_pkg.is_dir() {
                    return Some((dir.to_path_buf(), venv_py, false));
                }
                search_dir = dir.parent();
            } else {
                break;
            }
        }
    }

    // 3. Fallback to hardcoded known workspace path if present
    let workspace = PathBuf::from(r"d:\AI-ResearchAssistant");
    let ws_venv = workspace.join(".venv").join("Scripts").join("python.exe");
    if ws_venv.is_file() {
        return Some((workspace, ws_venv, false));
    }

    None
}

fn spawn_backend() -> Option<Child> {
    if is_backend_running() {
        println!("[Tauri] Backend is already running on port 8765.");
        return None;
    }

    if let Some((work_dir, exe_path, is_standalone)) = find_project_and_python() {
        println!(
            "[Tauri] Spawning backend from {:?} with executable {:?}",
            work_dir, exe_path
        );

        let mut cmd = Command::new(&exe_path);
        if is_standalone {
            // Standalone binary runs directly
            cmd.current_dir(&work_dir);
        } else {
            // Python script runs with uvicorn
            cmd.current_dir(&work_dir)
                .args(["-m", "uvicorn", "agent.server:app", "--host", "127.0.0.1", "--port", "8765"]);
        }

        #[cfg(target_os = "windows")]
        {
            cmd.creation_flags(CREATE_NO_WINDOW);
        }

        match cmd.spawn() {
            Ok(child) => {
                println!("[Tauri] Backend process started successfully (PID: {}).", child.id());
                Some(child)
            }
            Err(e) => {
                eprintln!("[Tauri] Failed to start backend process: {}", e);
                None
            }
        }
    } else {
        eprintln!("[Tauri] Could not locate backend executable or python .venv.");
        None
    }
}

fn main() {
    let backend_child = spawn_backend();

    tauri::Builder::default()
        .manage(BackendManager {
            child: Mutex::new(backend_child),
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let state: tauri::State<'_, BackendManager> = window.state();
                if let Ok(mut lock) = state.child.lock() {
                    if let Some(mut child) = lock.take() {
                        let _ = child.kill();
                    }
                };
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
