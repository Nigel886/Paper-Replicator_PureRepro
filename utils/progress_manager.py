import asyncio
import threading
from typing import Dict, List

class ProgressTracker:
    """
    A simple singleton-like manager to store and broadcast task progress via SSE.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressTracker, cls).__new__(cls)
            cls._instance.task_queues: Dict[str, asyncio.Queue] = {}
            cls._instance.loop = None
            # 增加全局停机标志
            cls._instance.shutdown_flag = threading.Event()
        return cls._instance

    def stop_all(self):
        """激活停机标志，停止所有正在运行的后台任务"""
        self.shutdown_flag.set()

    def is_shutdown(self):
        return self.shutdown_flag.is_set()

    def reset_shutdown(self):
        self.shutdown_flag.clear()

    def get_queue(self, task_id: str) -> asyncio.Queue:
        # Capture the running loop from the main thread when a queue is requested
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
            
        if task_id not in self.task_queues:
            self.task_queues[task_id] = asyncio.Queue()
        return self.task_queues[task_id]

    def update_progress(self, task_id: str, message: str, step: int = 0, total_steps: int = 0):
        """
        Pushes a progress message to the task's queue in a thread-safe manner.
        """
        if task_id in self.task_queues:
            data = {"message": message, "step": step, "total_steps": total_steps}
            
            # If we have a loop and it's running, use call_soon_threadsafe to push from any thread
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.task_queues[task_id].put_nowait, data)
            else:
                # Fallback (mostly for startup/tests)
                try:
                    self.task_queues[task_id].put_nowait(data)
                except Exception:
                    pass

    def remove_task(self, task_id: str):
        if task_id in self.task_queues:
            del self.task_queues[task_id]

# Global instance
progress_tracker = ProgressTracker()
