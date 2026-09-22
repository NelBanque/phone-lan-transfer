# Engineering Decisions

This log records decisions made during the project. Entries describe the current direction and may be revised when testing reveals a better approach.

| Decision | Why | Alternative considered | Trade-off |
| --- | --- | --- | --- |
| Run a local web server on the receiving computer and use a browser on the phone. | The phone needs no installed app, the transfer stays on the local network, and the same web architecture can support multiple platforms. | Build separate native mobile apps. | Both devices must be able to reach each other; local HTTP has security limits and browser behavior varies. |
| Build a safe upload MVP before adding HEIC conversion, EXIF sorting, and duplicate detection. | A smaller first version is easier to test and explain. | Add media processing from the start. | The MVP will preserve original files without organizing or converting them. |
| Keep engineering decisions public and interview study notes private. | Reviewers can inspect the reasoning without personal practice material. | Publish every working note. | Private notes must be backed up separately from the Git repository. |
| Manage the Python project with `pyproject.toml`, `uv`, and a `src/` layout. | The project has explicit metadata, reproducible dependencies, and a clear separation between application code and repository files. | Use `venv` and `pip` manually with a `requirements.txt` file. | Contributors need `uv`, and the project may need build-system configuration later if it becomes an installable package. |
| Use FastAPI with uvicorn and begin with a `GET /health` endpoint. | Type hints, automatic JSON responses, and in-process HTTP testing provide a small but testable server foundation. | Use Flask or Python's standard HTTP server. | FastAPI and its ASGI stack add dependencies and asynchronous concepts that must be understood. |
| Design for mobile devices with modern browsers and Windows, macOS, and Linux receivers, while validating one combination at a time. | The web and Python stack is portable, and a broader tool is more useful without requiring separate mobile apps. | Keep the product limited to iPhone and Windows. | The compatibility test matrix is larger, and packaging, paths, permissions, formats, and firewalls differ by platform. |
