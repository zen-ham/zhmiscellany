import os, signal, importlib
import zhmiscellany.math
import zhmiscellany.string
import zhmiscellany.processing
import zhmiscellany.mousekb
import zhmiscellany.fileio
import time, hashlib, ctypes
import keyboard
import random, string, copy
import keyword, builtins, inspect

# support backwards compatibility
click_pixel = zhmiscellany.mousekb.click_pixel
type_string = zhmiscellany.mousekb.type_string
scroll = zhmiscellany.mousekb.scroll
get_mouse_xy = zhmiscellany.mousekb.get_mouse_xy
KEY_CODES = zhmiscellany.mousekb.KEY_CODES


def die():
    os.kill(os.getpid(), signal.SIGTERM)


def show_progress(things, total_things, extra_data='', smart_ratelimit=False, max_prints=1000):
    do_print = True

    if smart_ratelimit:
        if total_things > max_prints:
            if not smart_every_nth(things, round(total_things/max_prints), total_things):
                do_print = False

    if do_print:
        print(f'\r{zhmiscellany.math.smart_percentage(things, total_things)}% {extra_data}', end='')
    if things == total_things:
        print('')


def every_nth(number, n):
    if number % n == 0:
        return True
    return False


def smart_every_nth(number, n, total):
    if number % n == 0:
        return True
    if number == total:
        return True
    return False


def calculate_eta(timestamps, total_timestamps):
    if not timestamps:
        return "Not enough data to calculate ETA."

    if total_timestamps <= len(timestamps):
        return "All timestamps recorded."

    # Calculate average time per timestamp
    total_time = timestamps[-1] - timestamps[0]
    average_time_per_timestamp = total_time / len(timestamps)

    # Calculate remaining time based on the average time per timestamp
    remaining_timestamps = total_timestamps - len(timestamps)
    estimated_remaining_time = remaining_timestamps * average_time_per_timestamp

    # Calculate the estimated arrival time
    current_time = time.time()
    estimated_arrival_time = current_time + estimated_remaining_time

    return zhmiscellany.string.timestamp_to_time(estimated_arrival_time)


def decide(options, text):
    output = input(f'{text} ({"/".join(options)})')
    while not output in options:
        output = input(f'{text} ({"/".join(options)})')
    return output


def import_module_from_path(path, module_name=None):
    if not module_name:
        module_name = zhmiscellany.string.get_universally_unique_string()
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base62_hash(anything):
    return zhmiscellany.string.convert_to_base62(int(int(hashlib.md5(anything if isinstance(anything, bytes) else str(anything).encode()).hexdigest(), 16)**0.5))


def md5_int_hash(anything):
    return int(hashlib.md5(anything if isinstance(anything, bytes) else str(anything).encode()).hexdigest(), 16)


def high_precision_sleep(duration):
    start_time = time.perf_counter()
    while True:
        elapsed_time = time.perf_counter() - start_time
        remaining_time = duration - elapsed_time
        if remaining_time <= 0:
            break
        if remaining_time > 0.02:  # Sleep for 5ms if remaining time is greater
            time.sleep(max(remaining_time/2, 0.0001))  # Sleep for the remaining time or minimum sleep interval
        else:
            pass


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception:
        return False


def die_on_key(key='f9', show_message=False):
    def _die_on_key(key):
        keyboard.wait(key)
        if show_message:
            print("Stopping the process because exit key was pressed.")
        die()
    zhmiscellany.processing.start_daemon(target=_die_on_key, args=(key,))


temp_folder = os.popen(r'echo %TEMP%').read().replace('\n', '')


def obfuscate_python(python_code_string, do_not_obfuscate_indent_block_comment='# DNO', remove_prints=True, remove_comments=True, add_lines=True, new_line_ratio=10):

    obf = python_code_string
    dno_sig = do_not_obfuscate_indent_block_comment
    dno_char = '2LAM67M4'

    if add_lines:
        remove_comments = True  # Sorry, I'm too lazy to implement this in a better way. Why would you not wanna remove comments anyway...

    if remove_prints or remove_comments:
        lines = obf.split('\n')
        for i, line in enumerate(lines):
            if remove_prints:
                if line.replace(' ', '').startswith('print('):
                    j = 0
                    for j, char in enumerate(line):
                        if char != ' ':
                            break
                    lines[i] = f'{" "*j}pass'
            has_dno = line.endswith(dno_sig)
            if remove_comments:
                lines[i] = lines[i].split('#')[0]
            if has_dno:
                lines[i] = lines[i] + ' ' + dno_char
        obf = '\n'.join(lines)
        lines = obf.split('\n')
        lines = [line for line in lines if not any([set(line) == set(j) for j in ['', ' ']])]
        obf = '\n'.join(lines)

    if add_lines:
        # gather reserved strings
        reserved = []
        reserved.extend(keyword.kwlist)  # keywords
        reserved.extend(dir(builtins))  # functions/constants
        reserved.extend([attr for attr in dir(object) if attr.startswith('__') and attr.endswith('__')])  # dunders
        reserved.extend([name for name, obj in vars(builtins).items() if inspect.isclass(obj) and issubclass(obj, BaseException)])  # exceptions
        # tokenize file
        base_splits = '\n\\!#$%&()*+,-./:;<=>?@[\]^`{|}~'
        var_splits = base_splits + ' "\''
        token_splits = base_splits + ' _'
        possible_existing_variables = zhmiscellany.string.multi_split(obf, list(var_splits))
        tokens = zhmiscellany.string.multi_split(obf, list(token_splits))
        tokens = [token for token in tokens if all([char in list(string.ascii_letters + string.digits + "_") for char in token])]
        tokens = [token for token in tokens if dno_char not in token]
        tokens = [token for token in tokens if token not in reserved]
        tokens = list(dict.fromkeys(tokens))
        number_tokens = [token for token in tokens if all([char in '1234567890' for char in token])]
        #number_tokens = [token for token in number_tokens if set(token) != set('0')]
        number_tokens = [token for token in number_tokens if not token.startswith('0')]
        all_tkns = copy.deepcopy(tokens)
        for i in number_tokens:
            tokens.remove(i)
        number_tokens = [num for num in number_tokens if len(str(num)) < 10000]


        base_rng = random.Random(0.26900750624933856)

        rngs = {
            'num_rng': random.Random(base_rng.random()),
            'var_name_rng': random.Random(base_rng.random()),
            'str_rng': random.Random(base_rng.random()),
            'lst_rng': random.Random(base_rng.random()),
            'new_rng': random.Random(base_rng.random()),
            'global_rng': random.Random(base_rng.random()),
            'match_rng': random.Random(base_rng.random()),
            'create_var_name': random.Random(base_rng.random()),
            'make_random_number': random.Random(base_rng.random()),
            'create_string': random.Random(base_rng.random()),
            'create_list': random.Random(base_rng.random()),
        }


        if not number_tokens:
            def make_random_number():
                ends = [10, 100, 1000]
                return rngs['make_random_number'].randint(0, rngs['make_random_number'].choice(ends))
            number_tokens = [make_random_number for i in range(round((len(obf.split('\n'))*new_line_ratio)/10))]
        total_new_lines = len(obf.split('\n'))*new_line_ratio

        def create_var_name(vars):
            while True:
                var = rngs['create_var_name'].choice(tokens)
                while True:
                    if var[0] in list('1234567890'):
                        break
                    if var not in possible_existing_variables and var not in vars['all']:
                        if rngs['create_var_name'].random() > 1/3:
                            return var
                    var = var + '_' + random.choice(tokens)

        def create_string(nds=None):
            stri = rngs['create_string'].choice(all_tkns)

            if not nds:
                stnds = ['"', "'", '"""', "'''"]
                nds = rngs['create_string'].choice(stnds)

            while True:
                if rngs['create_string'].random() > 1/3:
                    stri = stri + ' ' + rngs['create_string'].choice(all_tkns)
                else:
                    return nds + stri + nds

        def create_list(vars, will_run=True):
            lst_str = '['
            elements = []
            end = 2
            if not will_run:
                end = 3
            chz = rngs['create_list'].randint(1, end)
            stnds = ['"', "'", '"""', "'''"]
            nds = rngs['create_list'].choice(stnds)
            while True:
                if rngs['create_list'].random() > 1/6:
                    match chz:
                        case 1:
                            elements.append(create_string(nds))
                        case 2:
                            elements.append(rngs['create_list'].choice(number_tokens))
                        case 3:
                            elements.append(rngs['create_list'].choice(vars['all']))
                else:
                    break
            lst_str = lst_str + ', '.join(elements)
            lst_str = lst_str + ']'
            return lst_str

        varis = {
            'added_lines': [],
            'all': [],
            'num': [],
            'str': [],
            'lst': [],
            'fun': [],
        }
        prev = ''

        rngs['gen_num_var'] = random.Random(base_rng.random())
        rngs['gen_str_var'] = random.Random(base_rng.random())
        rngs['gen_lst_var'] = random.Random(base_rng.random())
        rngs['rand_num'] = random.Random(base_rng.random())
        rngs['rand_var'] = random.Random(base_rng.random())
        rngs['rand_loop'] = random.Random(base_rng.random())
        rngs['rand_num_add'] = random.Random(base_rng.random())
        rngs['rand_num_sub'] = random.Random(base_rng.random())
        rngs['rand_str'] = random.Random(base_rng.random())
        rngs['rand_print'] = random.Random(base_rng.random())
        rngs['rand_lst'] = random.Random(base_rng.random())
        rngs['add_pass'] = random.Random(base_rng.random())
        rngs['add_random_line'] = random.Random(base_rng.random())
        rngs['rand_var_add'] = random.Random(base_rng.random())
        rngs['rand_var_sub'] = random.Random(base_rng.random())
        rngs['gen_other_var'] = random.Random(base_rng.random())
        rngs['rand_func'] = random.Random(base_rng.random())
        rngs['rand_call_func'] = random.Random(base_rng.random())

        dno_indent = None

        for i, line in enumerate(lines):
            indent = 0
            for char in line:
                if char == ' ':
                    indent += 1
                else:
                    break
            single_indent = 4 if indent % 4 == 0 else 2
            varis['indent'] = indent

            if line.endswith(dno_char) or indent == dno_indent:
                dno_indent = indent
                continue
            else:
                dno_indent = None


            def gen_num_var(vars):

                if 1 / 4 > rngs['gen_num_var'].random() and vars['num']:
                    cvar = rngs['gen_num_var'].choice(vars['num'])
                else:
                    cvar = create_var_name(vars)
                    vars['num'].append(cvar)
                    vars['all'].append(cvar)

                return cvar

            def gen_str_var(vars):

                non_num = []
                non_num.extend(vars['str'])
                non_num.extend(vars['lst'])

                if 1 / 4 > rngs['gen_str_var'].random() and non_num:
                    cvar = rngs['gen_str_var'].choice(non_num)
                else:
                    cvar = create_var_name(vars)
                    vars['str'].append(cvar)
                    vars['all'].append(cvar)

                return cvar

            def gen_lst_var(vars):

                non_num = []
                non_num.extend(vars['str'])
                non_num.extend(vars['lst'])

                if 1 / 4 > rngs['gen_lst_var'].random() and non_num:
                    cvar = rngs['gen_lst_var'].choice(non_num)
                else:
                    cvar = create_var_name(vars)
                    vars['lst'].append(cvar)
                    vars['all'].append(cvar)

                return cvar

            def gen_func_var(vars):
                cvar = create_var_name(vars)
                vars['fun'].append(cvar)
                vars['all'].append(cvar)

                return cvar

            def gen_other_var(vars):
                cvar = create_var_name(vars)
                vars['all'].append(cvar)
                return cvar

            while rngs['global_rng'].random() > 1/(new_line_ratio*2) and (not any([prev.endswith(char) for char in list(' ,\\[{(')+reserved])) and (not any([char in line for char in ':'])):

                def rand_num(vars, will_run=True):  # var (new/old) to random int
                    cvar = gen_num_var(vars)
                    vars['added_lines'].append((i, f"{' ' * vars['indent']}{cvar} = {rngs['rand_num'].choice(number_tokens)}"))
                    return cvar

                def rand_var(vars, will_run=False):  # var (new/old) to random previous var
                    if will_run:
                        raise Exception('This should not be possible')

                    if vars['all']:
                        ev = rngs['rand_var'].choice(vars['all'])
                    else:
                        add_random_line(vars, will_run)
                        return

                    if ev in vars['num']:
                        cvar = gen_num_var(vars)
                    elif ev in vars['str']:
                        cvar = gen_str_var(vars)
                    elif ev in vars['lst']:
                        cvar = gen_lst_var(vars)
                    else:
                        cvar = gen_other_var(vars)

                    vars['added_lines'].append((i, f"{' ' * vars['indent']}{cvar} = {ev}"))
                    return cvar

                def rand_loop(vars, cvar, will_run=True):
                    if rngs['rand_loop'].random() > 1/(new_line_ratio/4):
                        return
                    end = 1
                    if cvar in vars['num']:
                        end = 2
                    choice = rngs['rand_loop'].randint(1, end)
                    match choice:
                        case 1:
                            vars['added_lines'].append((i, f"{' ' * vars['indent']}while {cvar}:"))
                        case 2:
                            vars['added_lines'].append((i, f"{' ' * vars['indent']}for {gen_other_var(vars)} in range(0, {cvar}):"))

                    vars['indent'] += single_indent
                    f = True
                    while rngs['rand_loop'].random() > 1 / (new_line_ratio * 2) or f:
                        add_random_line(vars, False)
                        f = False
                    vars['indent'] -= single_indent

                def rand_func(vars, will_run=True):
                    if rngs['rand_func'].random() > 1/(new_line_ratio):
                        add_random_line(vars, will_run)
                        return
                    cvar = gen_func_var(vars)
                    ev = []
                    while rngs['rand_func'].random() < 1/3:
                        ev.append(create_var_name(vars))
                    ev = ', '.join(ev)
                    vars['added_lines'].append((i, f"{' ' * vars['indent']}def {cvar}({ev}):"))
                    vars['indent'] += single_indent
                    cvars = []
                    while rngs['rand_func'].random() > 1 / (new_line_ratio * 2) or len([e for e in cvars if e]) == 0:
                        cvars.append(add_random_line(vars, will_run))
                    cvars = [e for e in cvars if e]
                    ev = []
                    f = True
                    while rngs['rand_func'].random() < 1/3 or f:
                        ev.append(rngs['rand_func'].choice(cvars))
                        f = False
                    ev = ', '.join(ev)
                    if rngs['rand_func'].random() > 1/3:
                        vars['added_lines'].append((i, f"{' ' * vars['indent']}return {ev}"))
                    vars['indent'] -= single_indent
                    return cvar

                def rand_call_func(vars, will_run=True):
                    if (not vars['fun']) or will_run:
                        add_random_line(vars, will_run)
                        return
                    func = rngs['rand_call_func'].choice(vars['fun'])
                    ev = []
                    while rngs['rand_call_func'].random() < 1/3:
                        ev.append(rngs['rand_call_func'].choice(vars['all']))
                    ev = ', '.join(ev)
                    vars['added_lines'].append((i, f"{' ' * vars['indent']}{func}({ev})"))

                def rand_num_add(vars, will_run=True):  # var (new/old) to random int + random int
                    cvar = gen_num_var(vars)
                    pos1 = rngs['rand_num_add'].choice(number_tokens)
                    pos2 = rngs['rand_num_add'].choice(number_tokens)
                    falsy = False
                    chz = rngs['rand_var_add'].randint(1, 3)
                    match chz:
                        case 1:
                            pos3 = '+'
                            if not (int(pos1) + int(pos2)): falsy = True
                        case 2:
                            pos3 = '-'
                            if not (int(pos1) - int(pos2)): falsy = True
                        case 3:
                            pos3 = '*'
                            if not (int(pos1) * int(pos2)): falsy = True

                    vars['added_lines'].append((i, f"{' ' * vars['indent']}{cvar} = {pos1} {pos3} {pos2}"))
                    if falsy:
                        rand_loop(vars, cvar)
                    return cvar

                def rand_var_add(vars, will_run=False):  # var (new/old) to random int + random int
                    if will_run:
                        raise Exception('This should not be possible')
                    cvar = gen_num_var(vars)

                    chz = rngs['rand_var_add'].randint(1, 2)
                    match chz:
                        case 1:pos1 = rngs['rand_var_add'].choice(number_tokens)
                        case 2:pos1 = rngs['rand_var_add'].choice(vars['all'])

                    chz = rngs['rand_var_add'].randint(1, 2)
                    match chz:
                        case 1:pos2 = rngs['rand_var_add'].choice(number_tokens)
                        case 2:pos2 = rngs['rand_var_add'].choice(vars['all'])

                    chz = rngs['rand_var_add'].randint(1, 7)
                    match chz:
                        case 1:pos3 = '+'
                        case 2:pos3 = '-'
                        case 3:pos3 = '/'
                        case 4:pos3 = '//'
                        case 5:pos3 = '%'
                        case 6:pos3 = '*'
                        case 7:pos3 = '**'

                    vars['added_lines'].append((i, f"{' ' * vars['indent']}{cvar} = {pos1} {pos3} {pos2}"))
                    return cvar

                def rand_str(vars, will_run=True):  # var (new/old) to random string
                    cvar = gen_str_var(vars)  # impossible for this to be falsy
                    vars['added_lines'].append((i, f"{' ' * vars['indent']}{cvar} = {create_string()}"))
                    return cvar

                def rand_print(vars, will_run=False):  # print 1 random var or 2 random string or 3 random int or 4 random list
                    if will_run:
                        raise Exception('This should not be possible')
                    cvar = gen_str_var(vars)
                    choice = rngs['rand_print'].randint(1, 4)
                    match choice:
                        case 1:
                            ev = rngs['rand_print'].choice(vars['all'])
                        case 2:
                            ev = create_string()
                        case 3:
                            ev = rngs['rand_print'].choice(number_tokens)
                        case 4:
                            ev = create_list(vars)
                    vars['added_lines'].append((i, f"{' ' * vars['indent']}print({ev})"))

                def rand_lst(vars, will_run=True):  # var (new/old) to random list
                    lst = create_list(vars, will_run)
                    cvar = gen_lst_var(vars)
                    vars['added_lines'].append((i, f"{' ' * vars['indent']}{cvar} = {lst}"))
                    if lst == '[]':  # this will miss some but vast majority will be caught
                        rand_loop(vars, cvar)
                    return cvar

                def add_pass(vars, will_run=True):  # pass
                    vars['added_lines'].append((i, f"{' ' * vars['indent']}pass"))

                run_vars = [rand_num, rand_num_add, rand_str, rand_lst, add_pass, rand_func]
                all_vars = run_vars + [rand_var, rand_print, rand_var_add, rand_call_func]

                def add_random_line(vars, will_run=True):
                    if will_run:
                        line_variations = run_vars
                    else:
                        line_variations = all_vars
                    variation = rngs['add_random_line'].choice(line_variations)
                    cvar = variation(vars, will_run)
                    return cvar

                add_random_line(varis)

            prev = line

        varis['added_lines'].reverse()
        for line in varis['added_lines']:
            lines.insert(line[0], line[1])
        obf = '\n'.join(lines)

        lines = obf.split('\n')
        for i, line in enumerate(lines):
            if line.endswith(dno_char):
                lines[i] = line.replace(dno_char, '')
            line_char_list = list(lines[i])
            while line_char_list[-1] == ' ':
                line_char_list.pop()
            lines[i] = ''.join(line_char_list)
        obf = '\n'.join(lines)
    return obf