# This file is part of beets.
# Copyright 2016, Adrian Sampson and Diego Moreda.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Aid in submitting information to MusicBrainz.

This plugin allows the user to print track information in a format that is
parseable by the MusicBrainz track parser [1]. Programmatic submitting is not
implemented by MusicBrainz yet.

[1] https://wiki.musicbrainz.org/History:How_To_Parse_Track_Listings
"""

import os
import pyratemp
import tempfile

from beets.autotag import Recommendation
from beets.plugins import BeetsPlugin
from beets.ui.commands import PromptChoice, manual_id
from beetsplug.info import print_data


class MBSubmitPlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()

        self.config.add({
            'format': '$track. $title - $artist ($length)',
            'threshold': 'medium',
        })

        # Validate and store threshold.
        self.threshold = self.config['threshold'].as_choice({
            'none': Recommendation.none,
            'low': Recommendation.low,
            'medium': Recommendation.medium,
            'strong': Recommendation.strong
        })

        self.register_listener('before_choose_candidate',
                               self.before_choose_candidate_event)

        # TODO configurable
        seeder_template = os.path.join(os.path.dirname(__file__), 'seeder.html')
        self.template = pyratemp.Template(filename=seeder_template)

    def before_choose_candidate_event(self, session, task):
        if task.rec <= self.threshold:
            return [
                    PromptChoice('p', 'Print tracks', self.print_tracks),
                    PromptChoice('f', 'seed submit Form', self.seed_form),
            ]

    def print_tracks(self, session, task):
        for i in sorted(task.items, key=lambda i: i.track):
            print_data(None, i, self.config['format'].as_str())

    def seed_form(self, session, task):
        html = self.template(items=task.items)
        fd, path = tempfile.mkstemp(suffix='.html')
        with os.fdopen(fd, 'w') as form:
            print(html, file=form)
        os.system(f"ssh void sh -c 'DISPLAY=:0 chrome file://{path}'")
        return manual_id(session, task)

