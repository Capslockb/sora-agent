"""
Sora Agent — Batch task runner for parallel execution.

Handles running multiple tasks in parallel with controlled concurrency.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


@dataclass
class BatchTask:
    """A single task in a batch."""
    id: str
    name: str
    coro: Coroutine
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, done, failed
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class BatchResult:
    """Result of a batch execution."""
    tasks: list[BatchTask]
    total: int
    succeeded: int
    failed: int
    duration_seconds: float


class BatchRunner:
    """
    Run multiple async tasks with controlled concurrency and progress reporting.
    """

    def __init__(
        self,
        max_concurrent: int = 4,
        console: Console | None = None,
        show_progress: bool = True,
    ):
        self.max_concurrent = max_concurrent
        self.console = console or Console()
        self.show_progress = show_progress
        self._tasks: list[BatchTask] = []
        self._semaphore: asyncio.Semaphore | None = None

    def add_task(
        self,
        task_id: str,
        name: str,
        coro: Coroutine,
        **metadata: Any,
    ) -> None:
        """Add a task to the batch."""
        self._tasks.append(BatchTask(id=task_id, name=name, coro=coro, metadata=metadata))

    def add_tasks(self, tasks: list[dict[str, Any]]) -> None:
        """Add multiple tasks at once."""
        for t in tasks:
            self.add_task(
                task_id=t["id"],
                name=t["name"],
                coro=t["coro"],
                **t.get("metadata", {}),
            )

    async def run(self) -> BatchResult:
        """Run all tasks with concurrency control."""
        if not self._tasks:
            return BatchResult([], 0, 0, 0, 0.0)

        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        start_time = datetime.utcnow()

        async def run_task(task: BatchTask) -> None:
            async with self._semaphore:
                task.status = "running"
                task.started_at = datetime.utcnow()
                try:
                    task.result = await task.coro
                    task.status = "done"
                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
                finally:
                    task.finished_at = datetime.utcnow()

        if self.show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console,
            ) as progress:
                progress_task = progress.add_task(
                    f"Running {len(self._tasks)} tasks...",
                    total=len(self._tasks),
                )

                async def tracked_run(task: BatchTask) -> None:
                    await run_task(task)
                    progress.advance(progress_task)

                await asyncio.gather(*[tracked_run(t) for t in self._tasks])
        else:
            await asyncio.gather(*[run_task(t) for t in self._tasks])

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        succeeded = sum(1 for t in self._tasks if t.status == "done")
        failed = sum(1 for t in self._tasks if t.status == "failed")

        return BatchResult(
            tasks=self._tasks,
            total=len(self._tasks),
            succeeded=succeeded,
            failed=failed,
            duration_seconds=duration,
        )

    def get_results(self) -> list[BatchTask]:
        """Get all task results."""
        return self._tasks

    def print_summary(self, result: BatchResult) -> None:
        """Print a summary of batch results."""
        self.console.print(f"\n[bold]Batch Complete[/bold] — {result.succeeded}/{result.total} succeeded, {result.failed} failed in {result.duration_seconds:.1f}s")

        for task in result.tasks:
            if task.status == "done":
                self.console.print(f"  [green]✓[/green] {task.name}")
            else:
                self.console.print(f"  [red]✗[/red] {task.name}: {task.error}")


async def run_batch(
    tasks: list[dict[str, Any]],
    max_concurrent: int = 4,
    console: Console | None = None,
) -> BatchResult:
    """Convenience function to run a batch of tasks."""
    runner = BatchRunner(max_concurrent=max_concurrent, console=console)
    runner.add_tasks(tasks)
    result = await runner.run()
    runner.print_summary(result)
    return result


__all__ = ["BatchTask", "BatchResult", "BatchRunner", "run_batch"]