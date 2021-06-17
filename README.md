[![Build Status](https://simc.arpae.it/moncic-ci/dballe-web/centos7.png)](https://simc.arpae.it/moncic-ci/dballe-web/)
[![Build Status](https://simc.arpae.it/moncic-ci/dballe-web/centos8.png)](https://simc.arpae.it/moncic-ci/dballe-web/)
[![Build Status](https://simc.arpae.it/moncic-ci/dballe-web/fedora32.png)](https://simc.arpae.it/moncic-ci/dballe-web/)
[![Build Status](https://simc.arpae.it/moncic-ci/dballe-web/fedora34.png)](https://simc.arpae.it/moncic-ci/dballe-web/)
[![Build Status](https://copr.fedorainfracloud.org/coprs/simc/stable/package/dballe-web/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/simc/stable/package/dballe-web/)

DB-All.e-web
===============================================================


Introduction
------------

DB-All.e-web is a GUI application to visualise and navigate DB-All.e databases.
(see https://github.com/ARPA-SIMC/dballe)

It also allows to perform simple editing tasks, and to graphically select and
export data subsets.

It's a new version of the old "provami" (see https://github.com/ARPA-SIMC/provami)

Usage
-----

```
Usage: /usr/bin/dballe-web [OPTIONS]

Options:

  --help                           show this help information

/usr/bin/dballe-web options:

  --db=dballe_url                  DB-All.e database to connect to
  --web-port                       listening port for web interface

/usr/lib64/python3.7/site-packages/tornado/log.py options:

  --log-file-max-size              max size of log files before rollover
                                   (default 100000000)
  --log-file-num-backups           number of log files to keep (default 10)
  --log-file-prefix=PATH           Path prefix for log files. Note that if you
                                   are running multiple tornado processes,
                                   log_file_prefix must be different for each
                                   of them (e.g. include the port number)
  --log-rotate-interval            The interval value of timed rotating
                                   (default 1)
  --log-rotate-mode                The mode of rotating files(time or size)
                                   (default size)
  --log-rotate-when                specify the type of TimedRotatingFileHandler
                                   interval other options:('S', 'M', 'H', 'D',
                                   'W0'-'W6') (default midnight)
  --log-to-stderr                  Send log output to stderr (colorized if
                                   possible). By default use stderr if
                                   --log_file_prefix is not set and no other
                                   logging is configured.
  --logging=debug|info|warning|error|none 
                                   Set the Python log level. If 'none', tornado
                                   won't touch the logging configuration.
                                   (default info)
```

Example `dballe_url` values:
 - `sqlite:file.sqlite` or `sqlite://file.sqlite`
 - `postgresql://user@host/db`
 - `mysql://[host][:port]/[database][?propertyName1][=propertyValue1]`…
 
See https://arpa-simc.github.io/dballe/general_ref/connect.html#url-syntax

Contact and copyright information
---------------------------------

The author of DB-ALLe is Enrico Zini <enrico@enricozini.com>

DB-All.e-web is Copyright (C) 2015-2021 ARPAE-SIMC <urpsim@arpae.it>

DB-All.e-web is licensed under the terms of the GNU General Public License version 2.0
