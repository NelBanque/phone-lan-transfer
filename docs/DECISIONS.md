# Engineering Decisions

This log records decisions made during the project. Entries describe the current direction and may be revised when testing reveals a better approach.

| Decision | Why | Alternative considered | Trade-off |
| --- | --- | --- | --- |
| Run a local web server on the PC and use Safari on the iPhone. | The iPhone needs no installed app, and the transfer stays on the local network. | Build an iPhone app. | Both devices must be able to reach each other; local HTTP has security limits. |
| Build a safe upload MVP before adding HEIC conversion, EXIF sorting, and duplicate detection. | A smaller first version is easier to test and explain. | Add media processing from the start. | The MVP will preserve original files without organizing or converting them. |
| Keep engineering decisions public and interview study notes private. | Reviewers can inspect the reasoning without personal practice material. | Publish every working note. | Private notes must be backed up separately from the Git repository. |
