# Sistema de Visión para Control de Robot NAO 🤖👁️

![Demo Preview](demo.gif) 

## Descripción 📝
Sistema de visión por computadora que detecta postura humana en tiempo real para controlar los movimientos de un robot NAO. Combina:
- Detección de landmarks corporales con MediaPipe
- Cálculo de ángulos articulares
- Interfaz visual con OpenCV
- Comunicación con NAO via sockets

## Características ✨
- 🎯 Detección precisa de postura (codos, hombros, cabeza)
- 📊 Visualización de ángulos en tiempo real
- 🔄 Dos modos de operación:
  - **Modo simulación** (solo visión)
  - **Modo real** (control físico del NAO)
- ⚡ Optimizado para tiempo real (30+ FPS)

## Requisitos 📋

### Hardware
- ✔️ Cámara web (720p o mejor)
- ✔️ Robot NAO (opcional para modo físico)

### Software
| Componente       | Versión  |
|------------------|----------|
| Python           | 3.10+    |
| OpenCV           | 4.5+     |
| MediaPipe        | 0.8.10+  |
| NumPy            | 1.21+    |
| NAOqi            | 2.1.4+   |

## Instalación 🛠️

1. Clona el repositorio:
```bash
git clone https://github.com/Sovero1/ImitacionNAO_Robot.git
cd Imitacion (separado en entorno 3.10 u otro)
cd RobotActua (separado en entorno 2.7 obligatorio )
```
| Archivo          | Entorno |
|------------------|---------|
| python robot.py  | 3.10+   |
| python main.py   | 2.7     |
