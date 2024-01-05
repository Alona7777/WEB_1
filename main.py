from collections import UserDict, defaultdict
import cmd
from datetime import date, datetime, timedelta
import pickle
import os
import re
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.table import Table
from abc import ABC, abstractmethod
import questionary
from termcolor import colored
from assistant_bot import Assistant, AddAssistant, EditAssistant, DeleteAssistant, BirthAssistant, ContactAssistant, ExitAssistant, NotesAssistant
from record import Record, AddressBook, Phone, Name, Email, Address, Birthday



console = Console()       
commands_text = "How can I help you? Please choose:"
commands_menu = {
    "CONTACT MENU": ContactAssistant(),
    "NOTE": NotesAssistant(),
    "BIRTH MENU": BirthAssistant(),
    "EXIT": ExitAssistant()
    }

table = Table(show_header = False, style = "cyan", width = 150)
table.add_column("", style = "bold magenta", justify = "center")
table.add_column("", style="yellow", justify="center")
table.add_column("", style="bold blue", justify="center")
table.add_column("", style="bold green", justify="center")
table.add_column("", style="red", justify="center")
table.add_row(commands_text, "CONTACT MENU", "NOTE", "BIRTH MENU", "EXIT")
console.print(table)


     
if __name__ == "__main__":
   
    # Основной цикл ввода
    while True:
        user_input = questionary.select('Choose an action:', choices=commands_menu.keys()).ask()
        commands_menu[user_input].handler()
        
