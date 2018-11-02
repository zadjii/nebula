import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from common_util import mylog


class HostEventHandler(FileSystemEventHandler):

    def __init__(self, host):
        self._host = host

    def dispatch(self, event):
        # todo:29 use these events directly, instead of scanning the tree
        self._host.acquire_lock()
        self._host.signal()
        super(HostEventHandler, self).dispatch(event)
        self._host.release_lock()

    def on_moved(self, event):
        super(HostEventHandler, self).on_moved(event)
        self._host.local_move_file(event.src_path, event.dest_path)

    def on_created(self, event):
        super(HostEventHandler, self).on_created(event)
        self._host.local_create_file(event.src_path)


    def on_deleted(self, event):
        super(HostEventHandler, self).on_deleted(event)
        self._host.local_delete_file(event.src_path)

    def on_modified(self, event):
        super(HostEventHandler, self).on_modified(event)
        self._host.local_modify_file(event.src_path)


class WatchdogWorker(object):

    def __init__(self, host):
        self.shutdown_requested = False
        # maps cloud roots -> the observer for that root
        self.observers = {}
        self.observer = Observer()
        self.observer.start()
        self.event_handler = HostEventHandler(host)

    def watch_path(self, cloud_root):
        mylog('Watching path <{}>'.format(cloud_root))
        self.observers[cloud_root] = \
            self.observer.schedule(self.event_handler, cloud_root, recursive=True)

    def watch_all_clouds(self, clouds):
        for mirror in clouds:
            if not (mirror.root_directory in self.observers.keys()):
                self.watch_path(mirror.root_directory)


