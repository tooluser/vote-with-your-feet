from hello import main


def describe_main():
    def it_prints_hello_message(capsys):
        main()
        captured = capsys.readouterr()
        assert "Hello from vote-with-your-feet!" in captured.out
