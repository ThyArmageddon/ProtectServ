#!/usr/bin/env  python2
# Copyright (C) 2014
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# Import time library
import time

# Import Twisted Libraries
from twisted.words.protocols import irc
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ClientFactory

# Import configuration file
import config


class ProtectServ(irc.IRCClient):
    '''
    This is the irc bot portion of the philobot

    This portion of the code will post a random question from
    a series of files filled with questions
    '''

    def __init__(self):
        self._admins = list(config.ADMINS)
        self._channel = config.CHANNEL
        self.priviledged_commands = {
            'die': self._die,
            'join': self._join,
            'part': self._part,
            'say': self._say,
        }
        self.unpriviledged_commands = {
            'source': self._show_source,
            'help': self._help,
        }

    def _get_nickname(self):
        return self.factory.nickname

    nickname = property(_get_nickname)

    def _cmsg(self, dest, msg):
        '''
        Writes the message in colors
        '''

        self.msg(dest, "%s%s" % (config.COLOR_CODE, msg))

    def _gmsg(self, msg):
        '''
        Write a message to the channel
        '''

        self._cmsg(self._channel, msg)

    def signedOn(self):
        '''
        Actions to perform a sigon to the server
        '''

        self.msg(config.SERVICES_NAME, '%s %s %s' %
                 (config.AUTHENTICATION_COMMAND,
                  config.SERVICES_ACCOUNT,
                  config.SERVICES_PASSWORD))
        time.sleep(5)
        self.join(self._channel)
        self._gmsg("Ahhhh, I am in %s" % self._channel)
        self._gmsg("It feels right back at home.")
        self.factory.running = True

    def joined(self, channel):
        '''
        Print to terminal when the bot joins a channel
        '''
        print("I joined %s." % channel)

    def userJoined(self, user, channel):
        '''
        Print user joined channel
        '''
        print("%s joined %s" % (user, channel))

    def userLeft(self, user, channel):
        '''
        Print user parted channel
        '''
        print("%s parted %s" % (user, channel))

    def userQuit(self, user, quitMessage):
        '''
        Print user quit with reason
        '''
        print("%s quit with reason: %s" % (user, quitMessage))

    def privmsg(self, user, channel, msg):
        '''
        Parses messages and replies to <COMMAND>question
        '''

        user, temp = user.split('!')
        print(channel + ": " + user + ": " + msg)
        # Strip off colors
        try:
            while not msg[0].isalnum() and not msg[0] == config.COMMAND:
                msg = msg[1:]
        except IndexError:
            return

        # Parse each incoming line and search for <COMMAND>question
        try:
            try:
                self._admins.index(user)
                is_admin = True
            except:
                is_admin = False

            if (msg[0] == config.COMMAND):
                command = msg.replace(config.COMMAND, '').split()[0]
                args = msg.replace(config.COMMAND, '').split()[1:]
                self.select_command(command, args, user, channel)
                return
            elif (msg.split()[0].find(self.nickname) == 0):
                command = msg.split()[1]
                args = msg.replace(self.nickname, '').split()[2:]
                self.select_command(command, args, user, channel)
                return
            # if not, ignore
            else:
                return

        except:
            return

    def noticed(self, user, channel, msg):
        print("NOTICE: %s: %s: %s" % (user, channel, msg))

    def ctcpquery(self, user, channel, msg):
        '''
        responds to ctcp requests.
        currently just reports them.
        '''
        print("ctcp received: " + user + ":" + channel + ": " +
              msg[0][0] + " " + msg[0][1])

    def _help(self, args, user, channel):
        '''
        Gives the admin the commands that they can use
        '''
        try:
            self._admins.index(user)
        except:
            self._cmsg(user, "Hello %s" % user)
            time.sleep(0.5)
            self._cmsg(user, "---------")
            time.sleep(0.5)
            self._cmsg(user, "Commands:")
            time.sleep(0.5)
            self._cmsg(user, "---------")
            time.sleep(0.5)
            for command in self.unpriviledged_commands:
                self._cmsg(user, "***  .%s" % command)
                time.sleep(0.5)
            return

        self._cmsg(user, "Hello %s" % user)
        time.sleep(0.5)
        self._cmsg(user, "-----------------------")
        time.sleep(0.5)
        self._cmsg(user, "Unpriviledged commands:")
        time.sleep(0.5)
        self._cmsg(user, "-----------------------")
        time.sleep(0.5)
        for command in self.unpriviledged_commands:
            self._cmsg(user, "***  .%s" % command)
            time.sleep(0.5)
        self._cmsg(user, "---------------------")
        time.sleep(0.5)
        self._cmsg(user, "Priviledged commands:")
        time.sleep(0.5)
        self._cmsg(user, "---------------------")
        time.sleep(0.5)
        for command in self.priviledged_commands:
            self._cmsg(user, "***  .%s" % command)
            time.sleep(0.5)

    def _show_source(self, args, user, channel):
        '''
        Returns the location of this bot
        '''
        self._cmsg(user, '*** The source code of this bot is available on github.')

    def select_command(self, command, args, user, channel):
        '''
        Divides commands between priviledged and unpriviledged
        '''
        print(command, args, user, channel)
        try:
            self._admins.index(user)
            is_admin = True
        except:
            is_admin = False

        if not is_admin and command in self.priviledged_commands.keys():
            self.msg(channel, "%s: My answer is still, why ?" % user)
            return
        elif is_admin and command in self.priviledged_commands.keys():
            self.priviledged_commands[command](args, user, channel)
        elif command in self.unpriviledged_commands.keys():
            self.unpriviledged_commands[command](args, user, channel)
        #else:
        #    self.describe(channel, '%slooks at %s oddly.' %
        #                  (config.COLOR_CODE, user))

    def _die(self, *args):
        '''
        Terminates the bot
        '''
        global reactor
        self.quit(message='This is ProtectServ, dying of self doubt.')
        reactor.stop()

    def _join(self, args, user, channel):
        #TODO:
        #   - Validate channel format
        #   - Add the ability to join multiple channels
        self.join(args[0])

    def _part(self, args, user, channel):
        #TODO:
        #   - Validate channel format
        #   - Add the ability to part multiple channels
        self.part(args[0])

    def _say(self, args, user, channel):
        #TODO:
        #   - Validate command format
        #   - Validate channel format
        #   - Check if bot is in that channel
        self._cmsg(args[0], ' '.join(args[1:]))


class ircbotFactory(ClientFactory):
    protocol = ProtectServ

    def __init__(self, nickname=config.DEFAULT_NICK):
        self.nickname = nickname
        self.running = False

    def clientConnectionLost(self, connector, reason):
        print("Lost connection (%s)" % (reason,))
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print("Could not connect: %s" % (reason,))
        connector.connect()


if __name__ == "__main__":
    if config.SERVER_SSL:
        reactor.connectSSL(config.SERVER, config.SERVER_PORT,
                           ircbotFactory(), ssl.ClientContextFactory())
    else:
        reactor.connectTCP(config.SERVER, config.SERVER_PORT, ircbotFactory())

    reactor.run()
