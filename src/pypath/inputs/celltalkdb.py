#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  This file is part of the `pypath` python module
#  Helps to translate from the mouse data to human data
#
#  Copyright
#  2014-2020
#  EMBL, EMBL-EBI, Uniklinik RWTH Aachen, Heidelberg University
#
#  File author(s): Dénes Türei (turei.denes@gmail.com)
#                  Nicolàs Palacio
#                  Olga Ivanova
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  Website: http://pypath.omnipathdb.org/
#


import os
import datetime
import collections

import bs4

import pypath.resources.urls as urls
import pypath.share.curl as curl
import pypath.share.cache as cache
import pypath.utils.taxonomy as taxonomy


def celltalkdb_download(filename = 'lr_pair', organism = 9606):
    """
    Downloads a file from CellTalkDB.

    :param str filename:
        The file name of the dataset to download. Possible values:
        lr_pair, gene_info, gene2ensembl, uniprot.
    :param int,str organism:
        Human and mouse supported, in case of incomprehensible value will
        fall back to human.

    :return:
        Generator yielding dataset specific records as named tuples.
    """

    taxid = taxonomy.ensure_common_name(organism)
    organism = taxid.lower() if taxid in {'Mouse', 'Human'} else 'human'

    cache_fname = 'celltalkdb_%s_%s' % (organism, filename)
    cache_path = os.path.join(cache.get_cachedir(), cache_fname)

    if os.path.exists(cache_path):

        result = curl.FileOpener(cache_path).result

    else:

        url = urls.urls['celltalkdb']['url']
        ref_url = urls.urls['celltalkdb']['ref_url']
        init_url = urls.urls['celltalkdb']['init_url']

        cookie = ''

        c_init = curl.Curl(
            init_url,
            silent = True,
            large = True,
            cache = False,
            follow = False,
            bypass_url_encoding = True,
            retries = 1,
            empty_attempt_again = False,
        )

        for h in c_init.resp_headers:

            if h.lower().startswith(b'set-cookie'):

                cookie = h.decode().split(':')[1].split(';')[0]

        soup = bs4.BeautifulSoup(c_init.fileobj, 'html.parser')
        form = soup.find('form', {'action': 'handler/download.php'})
        inputs = dict(
            (
                field.attrs['name'],
                field.attrs['value']
            )
            for field in form.find_all('input')
        )

        inputs['ref'] = ref_url
        inputs['filename'] = '%s_%s.txt' % (organism, filename)

        c = curl.Curl(
            url = url,
            cache = cache_path,
            post = inputs,
            silent = False,
            large = True,
            debug = True,
            req_headers = [
                'Cookie: %s' % cookie,
                'Referer: http://tcm.zju.edu.cn/celltalkdb/download.php',
            ],
        )

        result = c.result

    header = next(result).strip().split('\t')

    record = collections.namedtuple('CellTalkDbRecord', header)

    for values in result:

        yield record(*values.strip().split('\t'))


def celltalkdb_interactions(organism = 9606):

    pass