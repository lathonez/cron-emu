#! /usr/bin/python3
""" Lyst tech test cron timing emulator """

# core python imports
import sys
import select

class Cron(object):
    """
        Cron Class
        Responsible for the time processing
    """

    def __init__(self):
        """
            Initialiser:
              - parse command line args
              - read in config from stdin
              - process each line of stdin
        """

        # Create our config helper
        config = Config()

        # parse the command line args into simulated_current_time
        self.sct = config.get_cla()

        # read config from stdin
        stdin = config.get_stdin()

        # for each config line we have, print when it should run
        for line in stdin:
            self._print_runtime(line)

    def _get_next_day(self, hour, minute):
        """ Get the next day the cron will run, be it today or tomorrow """

        # wildcard is a special case
        if hour == '*':
            # will always be tomorrow if we're in the 23rd hour
            if self.sct['hour'] == 23:
                return 'tomorrow'

            return 'today'

        # we're not the wildcard if we've got this far..

        # less than the current hour is always tomorrow
        if hour < self.sct['hour']:
            return 'tomorrow'

        # equal current hour can be tomorrow if we've overrun in minutes
        if (hour == self.sct['hour'] and minute < self.sct['minute']):
            return 'tomorrow'

        # all other cases are today
        return 'today'

    def _get_next_hour(self, hour, minute):
        """ Get the next hour the cron will run """

        # if the hour is not a wildcard, the next time we run it is always that hour
        if hour != '*':
            return hour

        # we are a wildcard

        if self.sct['minute'] < minute:
            # we're supposed to run in the current hour
            return self.sct['hour']

        # not running in the current hour, so will either be next hour or 00 if we've hit end of day
        if self.sct['hour'] == 23:
            return 00

        return self.sct['hour'] + 1

    @classmethod
    def _get_next_minute(cls, minute):
        """ Get the next minute the cron will run """

        # if the minute is a wildcard and we're not running it, next run is zero
        if minute == '*':
            return 0

        # otherwise it's just the minute
        return minute

    def _print_runtime(self, line):
        """ Print the run time for a given line of stdin """

        if self._run_now(line):
            # Running now is a simple case so remove it to simplify the logic
            hour = self.sct['hour']
            minute = self.sct['minute']
            day = 'today'
        else:
            # We're not running now, so we need to figure out when we are running
            hour = self._get_next_hour(line['hour'], line['minute'])
            minute = self._get_next_minute(line['minute'])
            day = self._get_next_day(hour, minute)

        print ('{:}:{:0>2d} {:} {:}'.format(hour, minute, day, line['command']))

    def _run_now(self, line):
        """ bool - do we run right this minute? """

        # not the current hour and not a wildcard - not running
        if (line['hour'] != self.sct['hour'] and line['hour'] != '*'):
            return False

        # not the current minute and a wildcard - not running
        if (line['minute'] != self.sct['minute'] and line['minute'] != '*'):
            return False

        # All other cases run immediately
        return True

class Config(object):
    """
        Config Class
        Responsible for parsing command line arguments and stdin
    """

    #
    # Public
    #

    def get_cla(self):
        """ check that we've got a current_time at argv[0] and we can parse it in to HH:MM """
        if len(sys.argv) != 2:
            self._print_usage_and_exit(1)

        return self._parse_sct(sys.argv[1])

    def get_stdin(self):
        """ read from stdin but don't block if nothing's available """

        config = []
        # non blocking read from stdin
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            if line:
                config.append(self._parse_stdin_line(line.rstrip('\r\n')))
            else:
                # an empty line means stdin has been closed
                return config

        if len(config) == 0:
            print('no configuration input provided')
            self._print_usage_and_exit(9)

        return config

    #
    # private
    #

    def _parse_int(self, possible_int, debug, exit_code):
        """ helper to parse an int and exit with a given code and debug on failure """
        try:
            rtn = int(possible_int)
        except ValueError:
            print('could not parse integer - invalid input: ' + debug)
            self._print_usage_and_exit(exit_code)

        return rtn

    def _parse_sct(self, sct):
        """ parse the simulated_current_time on argv[1] """

        spl = sct.split(':')

        if len(spl) != 2:
            print('could not parse simulated_current_time - format should be HH:MM')
            self._print_usage_and_exit(2)

        spl[0] = self._parse_int(spl[0], 'HH', 3)
        spl[1] = self._parse_int(spl[1], 'MM', 4)

        if (spl[0] < 0 or spl[0] > 23):
            print('could not parse simulated_current_time hour - {0} out of range'.format(spl[0]))
            self._print_usage_and_exit(4)

        if (spl[1] < 0 or spl[1] > 59):
            print('could not parse simulated_current_time minute - {0} out of range'.format(spl[1]))
            self._print_usage_and_exit(5)

        return {
            'hour': spl[0],
            'minute': spl[1]
        }

    def _parse_stdin_line(self, config_line):
        """ parse a config line received from stdin """
        spl = config_line.split(' ')

        if config_line == '':
            print('empty config line')
            self._print_usage_and_exit(12)

        if spl[0] != "*":
            spl[0] = self._parse_int(spl[0], 'minute column {0}'.format(config_line), 7)
            if (spl[0] < 0 or spl[0] > 59):
                print('could not parse minute column - {0} out of range'.format(spl[0]))
                self._print_usage_and_exit(10)

        if spl[1] != "*":
            spl[1] = self._parse_int(spl[1], 'hour column {0}'.format(config_line), 8)
            if (spl[1] < 0 or spl[1] > 23):
                print('could not parse hour column - {0} out of range'.format(spl[0]))
                self._print_usage_and_exit(11)

        return {
            'minute': spl[0],
            'hour': spl[1],
            'command': spl[2]
        }

    @classmethod
    def _print_usage_and_exit(cls, exit_code):
        """ helper to print usage and exit with an error code """
        print('usage cron.py <simulated_current_time HH:MM> < config')
        sys.exit(exit_code)

# run the script
Cron()