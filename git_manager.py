import io
import os

try:
    from dulwich import porcelain
except ImportError:
    porcelain = None


class GitManager:
    """
    A Git Manager that uses pure Python (dulwich) to handle repository state.
    It does not rely on system 'git' binaries, making it secure and highly portable.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _check_dulwich(self):
        if porcelain is None:
            raise ImportError(
                "dulwich library is not installed. Please install it using 'pip install dulwich'"
            )

    def init(self) -> str:
        """Initialize a new git repository."""
        self._check_dulwich()
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            porcelain.init(self.repo_path)
            return "Repository initialized successfully."
        return "Repository already initialized."

    def status(self) -> str:
        """Get repository status."""
        self._check_dulwich()
        try:
            status_result = porcelain.status(self.repo_path)
            output = []

            staged, unstaged, untracked = status_result

            # format staged changes
            if staged.get("add") or staged.get("delete") or staged.get("modify"):
                output.append("Staged changes:")
                for f in staged.get("add", []):
                    output.append(f"  Added: {f.decode('utf-8')}")
                for f in staged.get("delete", []):
                    output.append(f"  Deleted: {f.decode('utf-8')}")
                for f in staged.get("modify", []):
                    output.append(f"  Modified: {f.decode('utf-8')}")

            if unstaged:
                output.append("Unstaged changes:")
                for f in unstaged:
                    output.append(f"  Modified: {f.decode('utf-8')}")

            if untracked:
                output.append("Untracked files:")
                for f in untracked:
                    output.append(f"  {f.decode('utf-8')}")

            if not output:
                return "Working tree clean."

            return "\n".join(output)
        except Exception as e:
            return f"Error getting status: {e}"

    def add_and_commit(self, message: str) -> str:
        """Stage all changes and commit."""
        self._check_dulwich()
        try:
            status_result = porcelain.status(self.repo_path)
            staged, unstaged, untracked = status_result

            paths_to_add = list(unstaged) + list(untracked)
            if paths_to_add:
                # dulwich add requires a list of bytes or strings relative to repo_path
                porcelain.add(self.repo_path, paths_to_add)

            commit_id = porcelain.commit(
                self.repo_path,
                message=message.encode("utf-8"),
                author=b"Agent <agent@local>",
                committer=b"Agent <agent@local>",
            )
            return f"Committed successfully. Commit ID: {commit_id.decode('utf-8')}"
        except Exception as e:
            return f"Error committing: {e}"

    def log(self, max_entries: int = 10) -> str:
        """View git commit history."""
        self._check_dulwich()
        try:
            outstream = io.BytesIO()
            porcelain.log(self.repo_path, max_entries=max_entries, outstream=outstream)
            return outstream.getvalue().decode("utf-8", errors="replace")
        except Exception as e:
            return f"Error getting log: {e}"

    def reset(self, commit_hash: str = "HEAD") -> str:
        """Revert the workspace to a previously committed version."""
        self._check_dulwich()
        try:
            porcelain.reset(
                self.repo_path, mode="hard", treeish=commit_hash.encode("utf-8")
            )
            return f"Successfully reset working tree to {commit_hash}"
        except Exception as e:
            return f"Error resetting: {e}"
