import datetime
import subprocess
import psutil


class SystemData:

    data: dict = {}

    def get(self):
        self.data['last_updated'] = self.timestamp
        self.data['cpu'] = self.cpu_usage
        self.data['mem'] = self.memory
        for i, bat in enumerate(list(self.battery)):
            self.data[f'bat{i}'] = bat
        return self.data

    @property
    def timestamp(self):
        """
        Populates 'last_updated' key in `data` current timestamp
        """
        return datetime.datetime.now().isoformat()

    @property
    def cpu_usage(self):
        """
        Populates 'cpu' key in `data` with average cpu usage
        """
        return psutil.cpu_percent()

    @property
    def memory(self):
        """
        Populates 'mem' key in `data` with average cpu usage
        """
        return psutil.virtual_memory().percent

    @property
    def battery(self):
        """
        Populates 'bat#' key in `data` with each battery's current remaining
        percentage
        """
        cmd = 'acpi -b'
        p = subprocess.run(cmd.split(), shell=True, capture_output=True)
        acpi_out, err = p.stdout.decode(), p.stderr.decode()
        # EXAMPLE OUTPUT:
        # Battery 0: Unknown, 99%
        # Battery 1: Discharging, 55%, 03:12:51 remaining

        if err:
            return []

        return map(lambda line: line.split(', ')[1][0:-1],
                acpi_out.rstrip().split('\n'))
