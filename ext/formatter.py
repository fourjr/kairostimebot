
import itertools
import inspect
import discord
from discord.ext.commands.core import GroupMixin, Command
from discord.ext.commands.errors import CommandError
from discord.ext.commands.formatter import HelpFormatter

class Paginator():
    'A class that aids in paginating code blocks for Discord messages.\n\n    Attributes\n    -----------\n    prefix: str\n        The prefix inserted to every page. e.g. three backticks.\n    suffix: str\n        The suffix appended at the end of every page. e.g. three backticks.\n    max_size: int\n        The maximum amount of codepoints allowed in a page.\n    '

    def __init__(self, prefix='', suffix='', max_size=2000):
        self.prefix = prefix
        self.suffix = suffix
        self.max_size = (max_size - len(suffix))
        self._current_page = [prefix]
        self._count = (len(prefix) + 1)
        self._pages = []

    def add_line(self, line='', *, empty=False):
        'Adds a line to the current page.\n\n        If the line exceeds the :attr:`max_size` then an exception\n        is raised.\n\n        Parameters\n        -----------\n        line: str\n            The line to add.\n        empty: bool\n            Indicates if another empty line should be added.\n\n        Raises\n        ------\n        RuntimeError\n            The line was too big for the current :attr:`max_size`.\n        '
        if (len(line) > ((self.max_size - len(self.prefix)) - 2)):
            raise RuntimeError(('Line exceeds maximum page size %s' % ((self.max_size - len(self.prefix)) - 2)))
        if (((self._count + len(line)) + 1) > self.max_size):
            self.close_page()
        self._count += (len(line) + 1)
        self._current_page.append(line)
        if empty:
            self._current_page.append('')
            self._count += 1

    def close_page(self):
        'Prematurely terminate a page.'
        self._current_page.append(self.suffix)
        self._pages.append('\n'.join(self._current_page))
        self._current_page = [self.prefix]
        self._count = (len(self.prefix) + 1)

    @property
    def pages(self):
        'Returns the rendered list of pages.'
        if (len(self._current_page) > 1):
            self.close_page()
        return self._pages

    def __repr__(self):
        fmt = '<Paginator prefix: {0.prefix} suffix: {0.suffix} max_size: {0.max_size} count: {0._count}>'
        return fmt.format(self)

class EmbedHelp(HelpFormatter):
    'The default base implementation that handles formatting of the help\n    command.\n\n    To override the behaviour of the formatter, :meth:`format`\n    should be overridden. A number of utility functions are provided for use\n    inside that method.\n\n    Parameters\n    -----------\n    show_hidden : bool\n        Dictates if hidden commands should be shown in the output.\n        Defaults to ``False``.\n    show_check_failure : bool\n        Dictates if commands that have their :attr:`Command.checks` failed\n        shown. Defaults to ``False``.\n    width : int\n        The maximum number of characters that fit in a line.\n        Defaults to 80.\n    '

    def __init__(self, show_hidden=False, show_check_failure=False, width=80):
        self.width = width
        self.show_hidden = show_hidden
        self.show_check_failure = show_check_failure

    def has_subcommands(self):
        'bool : Specifies if the command has subcommands.'
        return isinstance(self.command, GroupMixin)

    def is_bot(self):
        'bool : Specifies if the command being formatted is the bot itself.'
        return (self.command is self.context.bot)

    def is_cog(self):
        'bool : Specifies if the command being formatted is actually a cog.'
        return ((not self.is_bot()) and (not isinstance(self.command, Command)))

    def shorten(self, text):
        'Shortens text to fit into the :attr:`width`.'
        if (len(text) > self.width):
            return (text[:(self.width - 3)] + '...')
        return text

    @property
    def max_name_size(self):
        'int : Returns the largest name length of a command or if it has subcommands\n        the largest subcommand name.'
        try:
            commands = (self.command.commands if (not self.is_cog()) else self.context.bot.commands)
            if commands:
                return max(map((lambda c: (len(c.name) if (self.show_hidden or (not c.hidden)) else 0)), commands.values()))
            return 0
        except AttributeError:
            return len(self.command.name)

    @property
    def clean_prefix(self):
        'The cleaned up invoke prefix. i.e. mentions are ``@name`` instead of ``<@id>``.'
        user = self.context.bot.user
        return self.context.prefix.replace(user.mention, ('@' + user.name))

    def get_command_signature(self):
        'Retrieves the signature portion of the help page.'
        result = []
        prefix = self.clean_prefix
        cmd = self.command
        parent = cmd.full_parent_name
        if (len(cmd.aliases) > 0):
            aliases = '|'.join(cmd.aliases)
            fmt = '{0}[{1.name}|{2}]'
            if parent:
                fmt = '{0}{3} [{1.name}|{2}]'
            result.append(fmt.format(prefix, cmd, aliases, parent))
        else:
            name = ((prefix + cmd.name) if (not parent) else (((prefix + parent) + ' ') + cmd.name))
            result.append(name)
        params = cmd.clean_params
        if (len(params) > 0):
            for (name, param) in params.items():
                if (param.default is not param.empty):
                    should_print = (param.default if isinstance(param.default, str) else (param.default is not None))
                    if should_print:
                        result.append('[{}={}]'.format(name, param.default))
                    else:
                        result.append('[{}]'.format(name))
                elif (param.kind == param.VAR_POSITIONAL):
                    result.append('[{}...]'.format(name))
                else:
                    result.append('<{}>'.format(name))
        return ' '.join(result)

    def get_ending_note(self):
        command_name = self.context.invoked_with
        return ''

    def filter_command_list(self):
        'Returns a filtered list of commands based on the two attributes\n        provided, :attr:`show_check_failure` and :attr:`show_hidden`. Also\n        filters based on if :meth:`is_cog` is valid.\n\n        Returns\n        --------\n        iterable\n            An iterable with the filter being applied. The resulting value is\n            a (key, value) tuple of the command name and the command itself.\n        '

        def predicate(tuple):
            cmd = tuple[1]
            if self.is_cog():
                if (cmd.instance is not self.command):
                    return False
            if (cmd.hidden and (not self.show_hidden)):
                return False
            if self.show_check_failure:
                return True
            try:
                return (cmd.can_run(self.context) and self.context.bot.can_run(self.context))
            except CommandError:
                return False
        iterator = (self.command.commands.items() if (not self.is_cog()) else self.context.bot.commands.items())
        return filter(predicate, iterator)

    def _add_subcommands_to_page(self, max_width, commands):
        for (name, command) in commands:
            if (name in command.aliases):
                continue
            entry = '  .{0:<{width}}      {1}'.format(name, command.short_doc, width=max_width)
            shortened = self.shorten(entry)
            self._paginator.add_line(shortened)

    def format_help_for(self, context, command_or_bot):
        'Formats the help page and handles the actual heavy lifting of how\n        the help command looks like. To change the behaviour, override the\n        :meth:`format` method.\n\n        Parameters\n        -----------\n        context : :class:`Context`\n            The context of the invoked help command.\n        command_or_bot : :class:`Command` or :class:`Bot`\n            The bot or command that we are getting the help of.\n\n        Returns\n        --------\n        list\n            A paginated output of the help command.\n        '
        self.context = context
        self.command = command_or_bot
        return self.format(context)

    def format(self, ctx):
        'Handles the actual behaviour involved with formatting.\n\n        To change the behaviour, this method should be overridden.\n\n        Returns\n        --------\n        list\n            A paginated output of the help command.\n        '
        self._paginator = Paginator()
        description = (self.command.description if (not self.is_cog()) else inspect.getdoc(self.command))
        if description:
            self._paginator.add_line(description, empty=True)
        if isinstance(self.command, Command):
            signature = self.get_command_signature()
            self._paginator.add_line(signature, empty=True)
            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)
            if (not self.has_subcommands()):
                self._paginator.close_page()
                for page in self._paginator.pages:
                    msg = page.strip().splitlines()
                    for (i, line) in enumerate(msg):
                        if (i == 0):
                            x = line.strip().strip('.')
                            msg[i] = (('``' + x) + '``')
                        if (not line):
                            del msg[i]
                    #print(msg)
                    em = discord.Embed(color=discord.Colour.orange(), title=msg[0])
                    try:
                        em.description = ''.join(msg[1:])
                    except:
                        pass
                    #print('OVER HERE', em)
                    return [em]
        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            return ((cog + ':') if (cog is not None) else 'Default:')
        if self.is_bot():
            data = sorted(self.filter_command_list(), key=category)
            for (category, commands) in itertools.groupby(data, key=category):
                commands = list(commands)
                if (len(commands) > 0):
                    self._paginator.add_line(category)
                self._add_subcommands_to_page(max_width, commands)
        else:
            self._paginator.add_line('Commands:')
            self._add_subcommands_to_page(max_width, self.filter_command_list())
        self._paginator.add_line()
        ending_note = self.get_ending_note()
        self._paginator.add_line(ending_note)
        author = ctx.author
        msg = ''
        for page in self._paginator.pages:
            page = page.strip('```cs')
            msg += (page + '\n')
        msg = msg.strip().splitlines()
        for (i, line) in enumerate(msg):
            if (not line.strip().endswith(':')):
                x = line.strip().strip('.')
                x = (ctx.prefix + x)
                msg[i] = (('`' + x) + '`')
        categs = []
        for (i, e) in enumerate(msg):
            if e.endswith(':'):
                categs.append(i)
        embeds = []
        categs_per_page = 4
        for i in range(len(categs)):
            if ((i % categs_per_page) == 0):
                if (i == 0):
                    em = discord.Embed(color=65535)
                    em.set_author(name='Help - Commands', icon_url=(author.avatar_url or author.default_avatar_url))
                else:
                    em = discord.Embed(color=65535, timestamp=ctx.message.timestamp)
            base = categs[i]
            try:
                end = categs[(i + 1)]
                p = msg[base:end]
            except:
                p = msg[base:]
            em.add_field(name=p[0], value='\n'.join(p[1:]))
            if ((i % categs_per_page) == 0):
                embeds.append(em)
        embeds[(len(embeds) - 1)].set_footer(text='{} commands'.format((len(msg) - len(categs))))
        return embeds
