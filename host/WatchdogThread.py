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
        # print event.event_type

        what = 'directory' if event.is_directory else 'file'
        # logging.info("Moved %s: from %s to %s", what, event.src_path,
        #              event.dest_path)
        mylog('$$$$$$$ MOVED $$$$$$$$$$ {} $$$$$$$$$$$$$$$$$$$$'.format(event.src_path), '7')

    def on_created(self, event):
        super(HostEventHandler, self).on_created(event)
        # print event.event_type

        what = 'directory' if event.is_directory else 'file'
        # logging.info("Created %s: %s", what, event.src_path)
        mylog('$$$$$$$ Created $$$$$$$$$$ {} $$$$$$$$$$$$$$$$$$$$'.format(event.src_path), '7')

    def on_deleted(self, event):
        super(HostEventHandler, self).on_deleted(event)
        # print event.event_type

        what = 'directory' if event.is_directory else 'file'
        # logging.info("Deleted %s: %s", what, event.src_path)
        mylog('$$$$$$$ Deleted $$$$$$$$$$ {} $$$$$$$$$$$$$$$$$$$$'.format(event.src_path), '7')

    def on_modified(self, event):
        super(HostEventHandler, self).on_modified(event)
        # print event.event_type

        what = 'directory' if event.is_directory else 'file'
        # logging.info("Modified %s: %s", what, event.src_path)
        mylog('$$$$$$$ Modified $$$$$$$$$$ {} $$$$$$$$$$$$$$$$$$$$'.format(event.src_path), '7')


class WatchdogWorker(object):

    def __init__(self, host):
        self.shutdown_requested = False

        # maps cloud roots -> the observer for that root
        self.observers = {}
        self.observer = Observer()
        self.observer.start()

        self.event_handler = HostEventHandler(host)

    def work_thread(self):
        # I don;t think I need this
        # It's possible that the observers manage their own threads
        pass

    def watch_path(self, cloud_root):
        mylog('Watching path <{}>'.format(cloud_root))
        self.observers[cloud_root] = \
            self.observer.schedule(self.event_handler, cloud_root, recursive=True)

    def watch_all_clouds(self, clouds):
        # mylog('unschedule_all 0')
        # self.observer.stop()

        # mylog('unschedule_all 1')
        # self.observer.unschedule_all()
        for mirror in clouds:
            if not (mirror.root_directory in self.observers.keys()):
                self.watch_path(mirror.root_directory)

        # mylog('unschedule_all 2')


