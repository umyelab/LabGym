def exitstatus(value):
    """Determine the exit status based on the SystemExit object's attrs.
   
    More accurately, this is the *provisional* exit status, because
    trouble during Python cleanup could produce a different exit code.
    See https://docs.python.org/3/library/sys.html .

    The SystemExit object's args attribute and code attribute are
    provided in the value attribute of pytest's ExceptionInfo object.

    The assertions in this function serve to confirm that the relationship 
    between the args and code attributes is correctly understood.
   
    Example
        with pytest.raises(SystemExit) as e:
            sys.exit(2)
        assert exitstatus(e.value) == 2
   
    Example
        with pytest.raises(SystemExit) as e:
            raise SystemExit('Trouble...')
        assert exitstatus(e.value) == 1
    """ 

    if len(value.args) == 0:
        assert value.code is None, 'exitstatus misunderstanding?'
        return 0
    elif len(value.args) == 1 and isinstance(value.args[0], int):
        assert value.code == value.args[0], 'exitstatus misunderstanding?'
        return value.args[0]
    elif len(value.args) == 1 and isinstance(value.args[0], str):
        assert value.code == value.args[0], 'exitstatus misunderstanding?'
        assert value.code == value.__str__(), 'exitstatus misunderstanding?'
        return 1
    else:
        # Irregular usage of sys.exit() or SystemExit() will produce 
        # exit status 1.
        #
        # If you want to trigger a unit test fail on irregular/
        # unconventional usage so you can change it, you can raise an 
        # exception here.
        raise Exception('Irregular usage of sys.exit() or SystemExit()')

        # Otherwise, the irregular usage does result in exit status 1, 
        # so this is faithful.
        assert value.code.__str__() == value.args.__str__(), 'exitstatus misunderstanding?'
        return 1
