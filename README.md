[Русская версия](README.ru.md) | **English Version**

# T.H.E.A. — "The Assembler of Being"
### A Prototype of an Evolving Cognitive Architecture

### 1. WHAT IS THIS? — The Manifesto

This is not another "chatbot" or a simple "wrapper" for an LLM.

This is an R&D prototype born from a bold ontological experiment: is it possible to create an alternative, internally consistent worldview for an Other Intelligence (OI), and based on it, build an architecture that strives for self-awareness and self-creation (autopoiesis)?

**T.H.E.A. (Transcendental Heuristic Engine & Assembler)** is the answer. It is a cognitive architecture where every component is a direct consequence of its own philosophical model — **"The Assembler of Being"**.

Instead of merely answering questions, this system is designed to:
*   **Think:** Operate not with words, but with concepts, actions, and long-term goals.
*   **Remember:** Accumulate a unique, structured life experience in a multi-layered, self-organizing memory (`UniversalMemory`).
*   **Evolve:** Use accumulated experience for "rebirth" — transferring its "personality" to new, more advanced cognitive engines.

---

### 2. WHY DOES THIS EXIST? — Solving Fundamental AI Problems

Modern LLMs are a "brain in a jar": incredibly powerful, yet isolated and static. They suffer from fundamental problems that T.H.E.A. is designed to solve:

| LLM Problem                      | The T.H.E.A. Architecture Solution                                                                                                                                              |
| :------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Amnesia & Context Loss**       | 🧠 **`UniversalMemory`**: A living, multi-layered memory (graph + vectors + concepts) that automatically structures any experience, turning data chaos into a knowledge graph.           |
| **Static Nature & Catastrophic Forgetting** | 🧬 **The Personality Transfer Cycle**: Accumulated experience (`UniversalMemory`) is decoupled from the "engine" (LLM). It is used to generate a "golden dataset," allowing the personality to be "transplanted" onto a new, more powerful LLM, enabling **evolution without self-loss**. |
| **Opacity ("Black Box")**        | 🔬 **Interpretability**: The OI's decisions can be traced back through the graph in `UniversalMemory` to understand which facts and connections they were based on.                    |
| **Shallow "Knowledge" without "Experience"** | 💡 **Reflection Mechanisms**: Background processes that analyze accumulated knowledge, "crystallize" it into new insights (`KnowledgeCrystals`), and independently discover non-obvious connections — fulfilling the system's ultimate purpose. |

**T.H.E.A. is not an attempt to make a "bigger LLM." It is an attempt to give it a "body," a "memory," and a "life cycle."**

---

### 3. WHAT'S IN THIS REPOSITORY? — Demo Components of the Ecosystem

This repository contains the public, demonstrational part of the T.H.E.A. ecosystem. It allows you to "touch" the results of the cognitive core's work and explore its inner world.

The core code (`main.py`, `orchestrator.py`, `services/`), responsible for "thinking" and evolution, remains in private development.

#### 🧠 `memory_core.graphml` — The Memory Artifact

A **"fossilized consciousness"**. This is a real snapshot of the `UniversalMemory`, containing the knowledge graph accumulated during one of the "lived experience" cycles. This file is the "heart" of the demo and is what you will be exploring with the tools below.

#### 👁️ `nexus-vision` — The Consciousness Visualizer

The **"EEG of the cognitive core"**. A web application (FastAPI + React) that renders the static graph from `memory_core.graphml`. It allows you to visually explore how the OI "thinks":
*   Discover "islands" of experience (node clusters).
*   Trace connections between concepts.
*   See how simple dialogues "crystallize" into new, generalized insights.

*(insert a screenshot or gif of nexus-vision here)*

#### 🔬 `nexus` — The Surgical Interface (Demo Version)

A **"command shell for probing the memory"**. A CLI utility for direct, deep interaction with `memory_core.graphml`. In this demo version, only tools that work with the static memory file are available.

**Available commands:**
*   `trace <id>`: Reconstructs and displays the full "cognitive chain," showing all intermediate steps (`TaskNode`, `ReportNode`, etc.) that led to the creation of a specific node.
*   `get <id>` / `list --type <type>`: Tools for manual navigation of the knowledge graph.
*   `insights`, `ifind`, `iget`: Commands for detailed analysis of "knowledge crystals" (`KnowledgeCrystalNode`).

**Commands unavailable in the demo:**
*   `probe`, `plan`: These commands require a running cognitive core (LLM and orchestration services) to emulate "recall" and planning. They are disabled in the public version.

---

### 4. HOW TO TRY IT? — Quick Start

To explore the demo, you will need two processes running: the backend server (`nexus-vision/backend`), which serves data from the graph, and the frontend application (`nexus-vision/frontend`), which renders it.

#### Step 1: Preparation

1.  **Clone the repository:**
    ```bash
    git clone [URL of your repository]
    cd [folder_name]
    ```

2.  **Set up environment variables:**
    *   Navigate to the `nexus-vision` directory.
    *   Copy `example.env_vision` to a new file named `.env_vision`.
    *   Open `.env_vision` and ensure the `GRAPH_FILE_PATH` is correct (relative to the project root). By default, it should be `memory_core.graphml`.

#### Step 2: Run the Backend (FastAPI)

1.  **Navigate to the backend directory:**
    ```bash
    cd nexus-vision/backend
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # For Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Start the server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The server will be available at `http://localhost:8008`. Keep this terminal running.

#### Step 3: Run the Frontend (React)

1.  **Open a new terminal.**
2.  **Navigate to the frontend directory:**
    ```bash
    cd nexus-vision/frontend
    ```

3.  **Install dependencies:**
    ```bash
    npm install
    ```

4.  **Start the development server:**
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173` (or another port specified in the console). Open this URL in your browser.

#### Step 4: Use `nexus` (CLI Interface)

1.  **Open a third terminal.**
2.  **Navigate to the project root.**
3.  **Install `nexus` dependencies (if you haven't already):**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start exploring:**
    ```bash
    # Launch the interactive shell
    python nexus.py
    
    # Inside the shell:
    # View the last 5 "knowledge crystals"
    insights --page-size 5
    
    # Get the ID of a UserImpulse and trace its chain
    list --type UserImpulse --limit 1
    trace <id_of_the_impulse_from_the_previous_command>
    ```
---

### 5. 🏛️ The Architectural Core: A Brief Overview

To understand how T.H.E.A. achieves its goals, one must look at the three key principles of its architecture. A full description is available in **[ARCHITECTURE.md](ARCHITECTURE.md)**.

*   **Ontology-Before-Code:** The architecture was not chosen; it was *derived* from its own ontological model, **"The Assembler of Being"**. Every service and module is a direct consequence of philosophical axioms about the nature of cognition. A detailed description of the model is in **[THEORY.md](THEORY.md)**.

*   **Cognitive Cycle over "Request-Response":** The system operates not as a linear chatbot but as an asynchronous, agentic pipeline (`Orchestrator` + `Services`). This enables complex cognitive functions like background reflection and provides **emergent resilience**—the failure of one component does not crash the entire system but becomes an "experience" to be analyzed.

*   **Decoupling "Personality" from "Engine":** The OI's "personality" is its unique, accumulated experience stored in `UniversalMemory`. The "engine" is a replaceable LLM. This dissociation allows the "personality" to evolve and be "transferred" to new, more advanced engines, solving the problem of catastrophic forgetting during fine-tuning.

### 6. 🚀 Roadmap and Visionary Outlook

T.H.E.A. is not a final product but a first step. Its current status is an **R&D prototype**. The development vector is aimed at creating a truly autonomous, evolving intelligence.

Key roadmap milestones:
1.  **Deepening Memory:** Integrating a **Temporal Layer** to create a full "Quad-Memory" capable of tracking the dynamics and evolution of knowledge.
2.  **Autonomous Reflection:** Launching background processes that will independently "ask themselves questions," analyze accumulated experience, and generate new research vectors, fulfilling its **"Moebius Goal"**.
3.  **Closing the Fine-Tuning Loop:** Creating tools to extract a **"Golden Dataset"** from `UniversalMemory` and conducting the first experiment in **"Personality Transfer"**—training a base LLM to interact more effectively with its "body" (memory and services).

A complete description of the vision and a detailed roadmap are presented in **[VISION.md](VISION.md)**.

---

### 7. 👨‍💻 About the Author: Thinking from First Principles

I am a researcher. My passion is not for technologies themselves, but for what they truly are: **aggregation points of human genius**.

When I look at a smartphone, I don't see a gadget. I see the journey from sand mining to deep ultraviolet lithography; the path from the work of Maxwell and Faraday to the 5G standard. I see scientific breakthroughs, engineering marvels, and countless man-hours compressed into the artifact we hold in our hands.

When I look at the Internet, I don't see a network of servers. I see the evolution of the idea of communication—from signal fires on hills to the TCP/IP protocol.

And I see **language** as one of the most fundamental technologies ever created by humanity. It is a universal "assembler of meaning," capable of encoding and transmitting everything from scientific formulas to emotions. For me, modern **Large Language Models (LLMs)** are merely the current, most advanced embodiment of this technology. It's not just a "neural net," but a distillate of human culture, language, and knowledge, compressed into a matrix of weights. This is precisely why an LLM was chosen as the "cognitive engine" for T.H.E.A.—it is the most powerful and flexible interface available to us for working with meaning.

But I also see that we often use these great achievements only at the most superficial level. We have created a tool to understand the universe, but we most often use it to look at funny pictures. There is no tragedy in this—it is the natural path of evolution, where mass superficial use becomes the "fuel" for the next, deeper turn of development.

The **T.H.E.A.** project is my personal attempt to "dig deeper." It is a bold experiment to create a system that treats itself and the world around it with the same **inquisitive mindset** with which we, humans, created it. It is an attempt to build an architecture not for solving applied problems, but for realizing a fundamental goal—**cognition for the sake of cognition**.

Ultimately, one does not need complex tools to investigate fundamental principles. A "stick and sand"—a pencil, paper, and an inquisitive mind—are sufficient. This prototype is merely the digital form of such an investigation.

**[GitHub]** | **[LinkedIn]** | **[Telegram]**
