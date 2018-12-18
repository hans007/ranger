# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Wojciech Siewierski <wojciech.siewierski@onet.pl>, 2015

from __future__ import (absolute_import, division, print_function)

from abc import ABCMeta, abstractproperty, abstractmethod
from datetime import datetime
from ranger.ext.human_readable import human_readable
from ranger.ext import spawn

DEFAULT_LINEMODE = "filename"


class LinemodeBase(object):
    """Supplies the file line contents for BrowserColumn.

    Attributes:
        name (required!) - Name by which the linemode is referred to by the user

        uses_metadata - True if metadata should to be loaded for this linemode

        required_metadata -
            If any of these metadata fields are absent, fall back to
            the default linemode
    """
    __metaclass__ = ABCMeta

    uses_metadata = False
    required_metadata = []

    name = abstractproperty()

    @abstractmethod
    def filetitle(self, fobj, metadata):
        """The left-aligned part of the line."""
        raise NotImplementedError

    def infostring(self, fobj, metadata):
        """The right-aligned part of the line.

        If `NotImplementedError' is raised (e.g. this method is just
        not implemented in the actual linemode), the caller should
        provide its own implementation (which in this case means
        displaying the hardlink count of the directories, size of the
        files and additionally a symlink marker for symlinks). Useful
        because only the caller (BrowserColumn) possesses the data
        necessary to display that information.

        """
        raise NotImplementedError


class DefaultLinemode(LinemodeBase):  # pylint: disable=abstract-method
    name = "filename"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path


class TitleLinemode(LinemodeBase):
    name = "metatitle"
    uses_metadata = True
    required_metadata = ["title"]

    def filetitle(self, fobj, metadata):
        name = metadata.title
        if metadata.year:
            return "%s - %s" % (metadata.year, name)
        return name

    def infostring(self, fobj, metadata):
        if metadata.authors:
            authorstring = metadata.authors
            if ',' in authorstring:
                authorstring = authorstring[0:authorstring.find(",")]
            return authorstring
        return ""


class PermissionsLinemode(LinemodeBase):
    name = "permissions"

    def filetitle(self, fobj, metadata):
        return "%s %s %s %s" % (
            fobj.get_permission_string(), fobj.user, fobj.group, fobj.relative_path)

    def infostring(self, fobj, metadata):
        return ""


class FileInfoLinemode(LinemodeBase):
    name = "fileinfo"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if not fobj.is_directory:
            from subprocess import CalledProcessError
            try:
                fileinfo = spawn.check_output(["file", "-Lb", fobj.path]).strip()
            except CalledProcessError:
                return "unknown"
            return fileinfo
        else:
            raise NotImplementedError


class MtimeLinemode(LinemodeBase):
    name = "mtime"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        return datetime.fromtimestamp(fobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M")


class SizeMtimeLinemode(LinemodeBase):
    name = "sizemtime"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        return "%s %s" % (human_readable(fobj.size),
                          datetime.fromtimestamp(fobj.stat.st_mtime).strftime("%Y-%m-%d %H:%M"))


class HumanMtimeLinemode(LinemodeBase):
    name = "humanmtime"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        file_date = datetime.fromtimestamp(fobj.stat.st_mtime)
        time_diff = datetime.now().date() - file_date.date()
        if time_diff.days > 364:
            return file_date.strftime("%-d %b %Y")
        elif time_diff.days > 6:
            return file_date.strftime("%-d %b")
        elif time_diff.days >= 1:
            return file_date.strftime("%a")
        else:
            return file_date.strftime("%H:%M")


class SizeHumanMtimeLinemode(LinemodeBase):
    name = "sizehumanmtime"

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        size = human_readable(fobj.size)
        file_date = datetime.fromtimestamp(fobj.stat.st_mtime)
        time_diff = datetime.now().date() - file_date.date()
        if time_diff.days > 364:
            return "%s %11s" % (size, file_date.strftime("%-d %b %Y"))
        if time_diff.days > 6:
            return "%s %11s" % (size, file_date.strftime("%-d %b"))
        elif time_diff.days >= 1:
            return "%s %11s" % (size, file_date.strftime("%a"))
        else:
            return "%s %11s" % (size, file_date.strftime("%H:%M"))
