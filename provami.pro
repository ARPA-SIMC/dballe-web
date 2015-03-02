######################################################################
# Automatically generated by qmake (2.01a) Wed Oct 1 16:40:17 2014
######################################################################

QT += core gui widgets webkitwidgets
CONFIG += link_pkgconfig c++11
PKGCONFIG += libdballe
TEMPLATE = app
TARGET = provami-qt
DEPENDPATH += .
INCLUDEPATH += .

# Input
HEADERS += provami/types.h \
           provami/highlight.h \
           provami/datagridmodel.h \
           provami/datagridview.h \
           provami/filtercombobox.h \
           provami/mapview.h \
           provami/model.h \
           provami/provamimainwindow.h \
           provami/recordlineedit.h \
           provami/stationgridmodel.h \
           provami/attrgridmodel.h \
           provami/dateedit.h \
    provami/rawquerymodel.h \
    provami/refreshthread.h \
    provami/progressindicator.h \
    provami/filters.h \
    provami/config.h \
    provami/mapcontroller.h
FORMS += provamimainwindow.ui
SOURCES += types.cpp \
           highlight.cpp \
           datagridmodel.cpp \
           datagridview.cpp \
           filtercombobox.cpp \
           main.cpp \
           mapview.cpp \
           model.cpp \
           provamimainwindow.cpp \
           recordlineedit.cpp \
           stationgridmodel.cpp \
           attrgridmodel.cpp \
           dateedit.cpp \
    rawquerymodel.cpp \
    refreshthread.cpp \
    progressindicator.cpp \
    filters.cpp \
    config.cpp \
    mapcontroller.cpp

DISTFILES += world.dat

# From the qantenna .pro files: http://qantenna.sourceforge.net/
unix {
    CONFIG += debug
    # Prefix: base instalation directory
    isEmpty(PREFIX){
        PREFIX = /usr/local
    }

    DEB_BUILD = $$system(echo \$DEB_BUILD_OPTIONS)
    contains(DEB_BUILD, nostrip){
        QMAKE_STRIP =:
    }

    # No point defining this, since deb/rpm build tools need to redefine PREFIX
    # at build time to install in the package build dirs.
    #DEFINES += PREFIX=\\\"$${PREFIX}\\\"
    #DEFINES += DATADIR=\\\"$$DATADIR\\\" PKGDATADIR=\\\"$$PKGDATADIR\\\"

    target.path = $${PREFIX}/bin

    data.path = $$PREFIX/share/provami
    data.files = world.dat

    DEFINES += DATADIR=\\\"$$PREFIX/share/provami\\\"

    INSTALLS += target data
}
