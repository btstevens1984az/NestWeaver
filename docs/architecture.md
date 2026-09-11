# Architecture

NestWeaver splits into three cooperating layers:

1. **Hardware** — Pi 5 + Hailo, mecanum base, 6-DoF arm, depth camera, e-stop/power  
2. **Edge software** — Python SDK (`nestweaver`) for sim/dev + safety; ROS 2 packages for robot bringup  
3. **Local cognition** — Ollama LLM + optional on-device Hailo vision (no cloud required)

```mermaid
flowchart TB
  subgraph Humans
    Voice[Voice / CLI / App]
  end

  subgraph Cognition["Local cognition (on-robot)"]
    Ollama[Ollama LLM]
    Hailo[Hailo vision HEF]
    VoicePipe[STT / TTS]
  end

  subgraph Autonomy["Autonomy & safety"]
    Orch[AutonomyOrchestrator]
    Safety[SafetyInterlock]
    Nav[Navigation / Nav2]
    Tidy[Tidy / Fetch behaviors]
  end

  subgraph Drivers["Drivers & kinematics"]
    Base[Mecanum base driver]
    Arm[Arm IK + driver]
    Perc[Depth perception pipeline]
  end

  subgraph Hardware
    Pi[Raspberry Pi 5]
    HAT[Hailo accelerator]
    Omni[Omni / mecanum base]
    Manip[6-DoF arm]
    Cam[Depth camera]
    Estop[E-stop + BMS]
  end

  Voice --> VoicePipe
  VoicePipe --> Ollama
  Ollama --> Orch
  VoicePipe --> Orch
  Orch --> Safety
  Safety --> Base
  Safety --> Arm
  Orch --> Nav
  Orch --> Tidy
  Nav --> Base
  Tidy --> Arm
  Perc --> Hailo
  Perc --> Orch
  Base --> Omni
  Arm --> Manip
  Perc --> Cam
  Hailo --> HAT
  Pi --- HAT
  Pi --- Estop
  Estop --> Safety
```

## Data flow (fetch bottle)

1. Perception captures RGB-D → Hailo (or stub) detects `bottle` → deprojects XYZ.  
2. Safety validates EE pose and joint soft limits.  
3. Arm IK solves grasp; gripper closes.  
4. Nav2 / orchestrator drives to delivery waypoint with collision + geofence checks.  
5. Place pose → open gripper. Optional voice confirmation via Ollama.

## Why both ROS 2 and a pure Python SDK?

- **ROS 2** — production robot runtime, Nav2, bag recording, multi-node isolation.  
- **Python SDK** — Day-1 laptop demos, unit tests, CI, and hardware bring-up scripts without sourcing an entire workspace.
