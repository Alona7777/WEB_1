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
from record import Record, AddressBook, Phone, Name, Email, Address, Birthday, Note
from abc import ABC, abstractmethod
import questionary
from termcolor import colored

# декоратор по исправлению ошибок.
def input_error(func):
    def inner(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except KeyError:
            return 'No user with this name'
        except ValueError:
            return 'Incorrect information entered'
        except IndexError:
            return 'Enter user name'
    return inner

class AssistantBot(ABC):
    
    @abstractmethod
    def handler(self):
        pass

# основное меню команд  
class Assistant(AssistantBot):
    def __init__(self):
        super().__init__()
        self.colors = 'cyan'
        self.console = Console()
       
        
    def handler(self):
        commands_text = "How can I help you? Please choose:"
        commands_menu = {
            "CONTACT MENU": [ContactAssistant,"yellow"],
            "NOTE": [NotesAssistant, "blue"],
            "BIRTH MENU": [BirthAssistant,"bold green"],
            "EXIT": [ExitAssistant, "red"],
            }
        self.table_menu(commands_menu, commands_text)
        result = self.handler_user_input(commands_menu)
        if result in commands_menu:
            commands_menu[result][0]()
            return 
      
    def handler_user_input(self, commands_menu):
        result = questionary.select('Choose an action:', choices=commands_menu.keys()).ask()
        return result
       
     
    def table_menu(self, commands, commands_text):
        table = Table(show_header = False, style = "cyan", width = 150)
        table.add_column("", style = "bold magenta", width = 50, justify = "center")  # Empty column for left border
        for option, values in commands.items() :
           if values[-1]:
               color = values[-1]
               table.add_column(option, style = color, width = len(option) + 5, justify = "center")

        row_values = [f"{commands_text}"]
        row_values.extend(option for option, values in commands.items() if values[-1])
        table.add_row(*row_values)
        self.console.print(table)  
            

# меню по работе с контактной книгой
class ContactAssistant(Assistant, AddressBook):
    def __init__(self):
        super().__init__()
        self.phone_book = AddressBook()
            
    def handler(self):
        if os.path.isfile(self.phone_book.file):  # запуск файла с сохранеными контактами!!!
            self.phone_book.read_from_file()
        commands_text = "How can I help you? Please choose:"
        add_menu = AddAssistant()
        edit_menu = EditAssistant()
        delete_menu = DeleteAssistant()
        exit_menu = ExitAssistant()
        commands_menu = {
            'ADD': [add_menu.handler, "cyan"],
            'EDIT': [edit_menu.handler, "blue"],
            'DELETE': [delete_menu.handler, "red"],
            'SEARCH': [self.search, "blue"],
            'SHOW ALL': [self.show_all, "blue"],
            'RETURN TO MAIN MENU': [Assistant, ""],
            'EXIT': [exit_menu.handler, ""]
            }
        self.table_menu(commands_menu, commands_text)
        result = self.handler_user_input(commands_menu)
        if result in commands_menu:
            commands_menu[result][0]()
            return 

            
    # вывод в таблицу rich       
    def table_print(self, record: Record):
        table = Table(title="Contact Information", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Name", style="red", justify="center")
        table.add_column("Phones", style="bold blue", justify="center")
        table.add_column("Birthday", style="bold green", justify="center")
        table.add_column("Email", style="bold blue", justify="center")
        table.add_column("Address", style="yellow", justify="center")
        table.add_column("Days to birthday", style="yellow", justify="center")
        phone_str = "\n".join(
            "; ".join(p.value for p in record.phones[i:i + 2]) for i in range(0, len(record.phones), 2))
        table.add_row(
            str(record.name.value),
            str(phone_str),
            str(record.birthday),
            str(record.email),
            str(record.address),
            str(record.days_to_birthday())
        )
        return table

    # отдельная функция по поиску рекорд, чтобы избежать ошибку с несущестующим контактом 
    @input_error
    def find_record(self):
        if os.path.isfile(self.phone_book.file):  # запуск файла с сохранеными контактами!!!
            self.phone_book.read_from_file()
        print('=' * 150)
        completer = WordCompleter(list(self.phone_book.keys()), ignore_case=True)
        name = prompt('Enter the name of an existing contact=> ', completer=completer)
        record: Record = self.phone_book.find(name)
        if record:
            return record
    
    # отдельная функция по saving рекорд
    @input_error    
    def save_record(self, record: Record):
        if os.path.isfile(self.phone_book.file):  # запуск файла с сохранеными контактами!!!
            self.phone_book.read_from_file()
        self.phone_book.add_record(record)
        self.phone_book.write_to_file()
        return
            
    # поиск по имени и по совпадениям
    @input_error
    def search(self):
        table = Table(title="Search results", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Name", style="red", justify="center")
        table.add_column("Phones", style="bold blue", justify="center")
        table.add_column("Birthday", style="bold green", justify="center")
        table.add_column("Email", style="bold blue", justify="center")
        table.add_column("Address", style="yellow", justify="center")
        table.add_column("Days to birthday", style="yellow", justify="center")
        while True:
            print('=' * 150)
            print(f'\033[38;2;10;235;190mEnter at least 3 letters or numbers to search or press ENTER to exit.\033[0m')
            res = input('Enter your text=>  ').lower()
            if res:
                result = self.phone_book.search(res)
                
                if result:
                    result = result.split('\n')
                    for item in result:
                        record = item.split(',')
                        table.add_row(record[0], record[1], record[2], record[3], record[4], record[5])
                        self.console.print(table)
                print(f'\033[38;2;10;235;190mNo matches found.\033[0m')        
            else:
                break
            

    # работа через интератор или показать все контакты
    def show_all(self):
        while True:
            table = Table(title="Contact Information", style="cyan", title_style="bold magenta", width = 100)
            table.add_column("Name", style="red", justify="center")
            table.add_column("Phones", style="bold blue", justify="center")
            table.add_column("Birthday", style="bold green", justify="center")
            table.add_column("Email", style="bold blue", justify="center")
            table.add_column("Address", style="yellow", justify="center")
            table.add_column("Days to birthday", style="yellow", justify="center")
            print('=' * 150)
            print(f'\033[38;2;10;235;190mEnter how many records to display or press ENTER to skip.\033[0m')
            item_number = input('Enter number=> ')
            if item_number.isdigit():
                if self.phone_book :
                    # Введено число
                    item_number = int(item_number)
                    metka = 0
                    # phones = 'Contacts:\n'
                    iteration_count = 0
                    for name, record in self.phone_book.data.items() :
                        phone_str = "\n".join(
                            "; ".join(p.value for p in record.phones[i :i + 2]) for i in range(0, len(record.phones), 2))
                        table.add_row(str(record.name.value),
                                      str(phone_str),
                                      str(record.birthday),
                                      str(record.email),
                                      str(record.address),
                                      str(record.days_to_birthday())
                                      )
                        iteration_count += 1
                        metka = 1

                        if iteration_count % item_number == 0 :
                            self.console.print(table)
                            metka = 0
                            table = Table(title = "Contact Information", style = "cyan", title_style = "bold magenta",
                                          width = 100)
                            table.add_column("Name", style = "red", justify = "center")
                            table.add_column("Phones", style = "bold blue", justify = "center")
                            table.add_column("Birthday", style = "bold green", justify = "center")
                            table.add_column("Email", style = "bold blue", justify = "center")
                            table.add_column("Address", style = "yellow", justify = "center")
                            table.add_column("Days to birthday", style = "yellow", justify = "center")

                    if metka == 1:
                        self.console.print(table)
                    return
                else:
                    print(f'\033[91mNo contacts.\033[0m')
            elif item_number.isalpha() :
                # Введены буквы
                print(f'You entered letters: {item_number}')
            else :
                if self.phone_book :
                    for name, record in self.phone_book.data.items() :
                        phone_str = "\n".join(
                            "; ".join(p.value for p in record.phones[i :i + 2]) for i in range(0, len(record.phones), 2))
                        table.add_row(str(record.name.value),
                                      str(phone_str),
                                      str(record.birthday),
                                      str(record.email),
                                      str(record.address),
                                      str(record.days_to_birthday())
                                      )
                    self.console.print(table)
                    return
                else:
                    print(f'\033[91mNo contacts.\033[0m')
                    return

    # выход из програмы и сохранение файла!
    def exit(self):
        self.phone_book.write_to_file()
        return   
 
# меню для работы по добавлению информации в контактную книгу              
class AddAssistant(ContactAssistant):
    def __init__(self):
        super().__init__()
      
    def handler(self):
        exit_menu = ExitAssistant()
        commands_text = "What would you like to add? Please choose:"
        commands_menu = {
            'CONTACT': [self.add_contact, "cyan"],
            'PHONE': [self.add_phone_menu, "blue"],
            'BIRTHDAY': [self.add_birthday_menu, "green"],
            'EMAIL': [self.add_email_menu, "blue"],
            'ADDRESS': [self.add_address_menu, "yellow"],
            'RETURN TO MAIN MENU': [Assistant, ""],
            'EXIT': [exit_menu.handler, ""],
            }
        self.table_menu(commands_menu, commands_text)
        result = self.handler_user_input(commands_menu)
        if result in commands_menu:
            commands_menu[result][0]()
            return 
        
    
    # добавление нового контакта
    @input_error
    def add_contact(self):
        name = input('Enter name=> ')
        record = Record(name)
        self.add_phone(record)
        self.add_birthday(record)
        self.add_email(record)
        self.add_address(record)
        self.save_record(record)
        contact = self.table_print(record)
        print(f'\033[92mYou have created a new contact:\033[0m')
        self.console.print(contact)
        return
    
    # добавление адреса   
    @input_error
    def add_address(self, record: Record):
        print(f'\033[38;2;10;235;190mEnter your address or press ENTER to skip.\033[0m')
        address = input('Enter address=> ')
        if address:
            record.add_address(address)
            self.save_record(record)
            print(f'\033[38;2;10;235;190mThe address {address} has been added.\033[0m')
            return
        else:
            return

    @input_error
    def add_address_menu(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found\033[0m')
                return
            elif record.address == None:
                self.add_address(record)
                self.console.print(self.table_print(record))
                return
            else:
                print('\033[91mThis contact has address.\033[0m')
                return

    # добавление даты дня рождения
    def add_birthday(self, record: Record):
        while True:
            try:
                print(f'\033[38;2;10;235;190mEnter the date of birth or press ENTER to skip.\033[0m')
                birth = input('Enter date of birth. Correct format: YYYY.MM.DD=> ')
                if birth:
                    record.add_birthday(birth)
                    self.save_record(record)
                    print(f'\033[38;2;10;235;190mThe date of birth {birth} has been added.\033[0m')
                    return
                else:
                    return
            except ValueError as e:
                print(e)

    @input_error
    def add_birthday_menu(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            elif record.birthday == None:
                self.add_birthday(record)
                self.console.print(self.table_print(record))
                return
            else:
                print('\033[91mThis contact has date of birth.\033[0m')
                return
            
    # добаваление email  
    @input_error
    def add_email(self, record: Record):
        while True:
            try:
                print(f'\033[38;2;10;235;190mEnter the email or press ENTER to skip.\033[0m')
                email = input('Enter email=> ')
                if email:
                    record.add_email(email)
                    self.save_record(record)
                    print(f'\033[38;2;10;235;190mThe email {email} has been added.\033[0m')
                    return
                else:
                    return
            except ValueError as e:
                print(e)

    @input_error
    def add_email_menu(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            elif record.email == None:
                self.add_email(record)
                self.console.print(self.table_print(record))
                return
            else:
                print('\033[91mThis contact has email.\033[0m')
                return
       
    # добавление номера телефона        
    @input_error
    def add_phone(self, record: Record):
        count_phone = 1
        while True:
            try:
                print(
                    f'\033[38;2;10;235;190mPlease enter the Phone Number {count_phone}, or press ENTER to skip.\033[0m')
                phone = input('Enter phone=> ')
                if phone:
                    record.add_phone(phone)
                    self.save_record(record)
                    print(f'\033[38;2;10;235;190mThe phone number {phone} has been added.\033[0m')
                    count_phone += 1
                else:
                    return
            except ValueError as e:
                print(e)

    @input_error
    def add_phone_menu(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            self.add_phone(record)
            self.console.print(self.table_print(record))
            return


# меню для работы по редактированию информации в контактной книге 
class EditAssistant(ContactAssistant):
    def __init__(self):
        super().__init__()
    
    def handler(self):
        exit_menu = ExitAssistant()
        commands_text = "What do you want to change? Please choose:"   
        commands_menu = {
            'NAME': [self.edit_name, "cyan"],
            'PHONE': [self.edit_phone, "blue"],
            'BIRTHDAY': [self.edit_birthday, "green"],
            'EMAIL': [self.edit_email, "blue"],
            'ADDRESS': [self.edit_address, "yellow"],
            'RETURN TO MAIN MENU': [Assistant, ""],
            'EXIT': [exit_menu.handler, ""],
            }
        self.table_menu(commands_menu, commands_text)
        result = self.handler_user_input(commands_menu)
        if result in commands_menu:
            commands_menu[result][0]()
            return 
    
    # изменение адреса
    @input_error
    def edit_address(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            AddAssistant.add_address(record)
            self.save_record(record)
            print(f'\033[38;2;10;235;190mYou changed the contact:\n\033[0m')
            self.console.print(self.table_print(record))
            return
        
    # изменение даты рождения
    @input_error
    def edit_birthday(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            self.console.print(self.table_print(record))
            AddAssistant.add_birthday(record)
            self.save_record(record)
            print(f'\033[38;2;10;235;190mYou changed the contact:\n\033[0m')
            self.console.print(self.table_print(record))
            return
        
    # изменение email      
    @input_error
    def edit_email(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            AddAssistant.add_email(record)
            self.save_record(record)
            print(f'\033[38;2;10;235;190mYou changed the contact:\n\033[0m')
            self.console.print(self.table_print(record))
            return    
     
    # изменение имени
    @input_error
    def edit_name(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            new_name = input('Enter new name=> ')
            if new_name:
                old_name = record.name.value
                self.phone_book.data[new_name] = self.phone_book.data.pop(old_name)
                record.name.value = new_name
                self.save_record(record)
                print(f'\033[38;2;10;235;190mName changed successfully from {old_name} to {new_name}.\n\033[0m')
                self.console.print(self.table_print(record))
                return
            else:
                return 
              
    # изменение телефона
    @input_error
    def edit_phone(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            self.console.print(self.table_print(record))
            old_phone = input('Enter the phone number you want to change=> ')
            new_phone = input('Enter the new phone number=> ')
            result = record.edit_phone(old_phone, new_phone)
            if result is None:
                print(f'\033[91mPhone: {old_phone} not found!\033[0m')
                return
            self.save_record(record)
            print(f'\033[38;2;10;235;190mYou changed the contact:\n\033[0m')
            self.console.print(self.table_print(record))
            return


# меню для работы по удалению информации в контактной книге       
class DeleteAssistant(ContactAssistant):
    def __init__(self):
        super().__init__()
    
    def handler(self):
        exit_menu = ExitAssistant()
        commands_text = "What do you want to delete? Please choose:"    
        commands_menu = {
            'CONTACT': [self.delete_contact, "cyan"],
            'PHONE': [self.delete_phone, "blue"],
            'BIRTHDAY': [self.delete_birthday, "green"],
            'EMAIL': [self.delete_email, "blue"],
            'ADDRESS': [self.delete_address, "yellow"],
            'RETURN TO MAIN MENU': [Assistant, ""],
            'EXIT': [exit_menu.handler, ""],
            }
        self.table_menu(commands_menu, commands_text)
        result = self.handler_user_input(commands_menu)
        if result in commands_menu:
            commands_menu[result][0]()
            return 
        
    # удаление адреса
    @input_error
    def delete_address(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            record.address = None
            self.save_record(record)
            print(f'\033[38;2;10;235;190mThe address was removed.\033[0m')
            self.console.print(self.table_print(record))
            return
        
    # удаление даты рождения
    @input_error
    def delete_birthday(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            record.birthday = None
            self.save_record(record)
            print(f'\033[38;2;10;235;190mThe date of birth was removed.\033[0m')
            self.console.print(self.table_print(record))
            return
        
    # удаление контакта
    @input_error
    def delete_contact(self):
         while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            self.console.print(self.table_print(record))
            print('\033[91mDo you really want to delete this contact? Please enter the number: 1.YES or press ENTER to skip.\033[0m')
            res = input('Enter your text=>  ').lower()
            if res in ('1', 'yes'):
                self.phone_book.delete(record.name.value)
                print(f'\033[38;2;10;235;190mThe contact {record.name.value} was removed.\033[0m')
                self.phone_book.write_to_file()
                return 
            else:
                return      

    # удаление email
    @input_error
    def delete_email(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            record.email = None
            self.save_record(record)
            print(f'\033[38;2;10;235;190mThe email was removed.\033[0m')
            self.console.print(self.table_print(record))
            return
 
    # удаление номера
    @input_error
    def delete_phone(self):
        while True:
            record = self.find_record()
            if not record:
                print('\033[91mThe contact was not found.\033[0m')
                return
            self.console.print(self.table_print(record))
            phone = input('Enter phone=> ')
            result = record.remove_phone(phone)
            print(f'\033[38;2;10;235;190mThe phone number {phone} was removed.\033[0m')
            self.save_record(record)
            print(f'\033[38;2;10;235;190mYou changed the contact:\n.\033[0m')
            self.console.print(self.table_print(record))
            return


# меню для работы с днями рождения из контактной книге
class BirthAssistant(ContactAssistant):
    def __init__(self):
        super().__init__()

        
    def handler(self):
        if os.path.isfile(self.phone_book.file):  # запуск файла с сохранеными контактами!!!
            self.phone_book.read_from_file()
        exit_menu = ExitAssistant()
        commands_text = "How can I help you? Please choose:"
        commands_menu = {
            'FOR THIS DAY': [self.birthdays_for_date_menu, "blue"],
            'THIS WEEK': [self.get_birthdays_per_week_menu, "blue"],
            'FOR A FEW DAYS': [self.birthday_in_given_days_menu, "blue"],
            'RETURN TO MAIN MENU': [Assistant, ""],
            'EXIT': [exit_menu.handler, ""],
        }
        self.table_menu(commands_menu, commands_text)
        result = self.handler_user_input(commands_menu)
        if result in commands_menu:
            commands_menu[result][0]()
            return 

    # список имен у кого день рождения на указанною дату
    def birthdays_for_date(self, day):
        date = datetime.strptime(day, '%Y.%m.%d').date()
        date_today = date.today()             
        contact_birth = []
        for n, rec in self.phone_book.data.items():
            name = n
            if rec.birthday:
                birth = rec.birthday.value.replace(year=date_today.year)
                if birth == date:
                    contact_birth.append(name)
            
        if len(contact_birth) == 0:
            print(f'\033[38;2;10;235;190mNo Birthday this day.\033[0m')
            return None
        return contact_birth

    # Displaying birthdays for the current date
    def birthdays_for_date_menu(self):
        table = Table(title="Birthdays information", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Name", style="red", justify="center")
        today_data = datetime.today().date()
        today_data_str = today_data.strftime('%Y.%m.%d')
        if not self.phone_book:
            print(f'\033[91mNo contacts.\033[0m')
            return
        else:
            birth = self.birthdays_for_date(today_data_str)
            if birth:
                s = ''
                for el in birth:
                    s += '| ' + el + ' |'
                table.add_row(s)
                self.console.print(table)

    # список имен у кого дни рождения на неделю от сегоднешней даты
    # {'Monday': ['Masha'], 'Tuesday': ['Pavel'], 'Wednesday': ['Stiv']}
    def get_birthdays_per_week(self):
        date_today = date.today()          
        birthday_per_week = []
        for n, rec in self.phone_book.data.items():
            if rec.birthday:
                name = f'{n}: {rec.birthday.value}'
                birth = rec.birthday.value.replace(year=date_today.year)
                if birth < date_today - timedelta(days=1):
                    birth = birth.replace(year=date_today.year+1)
                day_week = birth.isoweekday()
                end_date = date_today + timedelta(days=7)
                if date_today <= birth <= end_date:
                    birthday_per_week.append([name, birth, day_week])
        if len(birthday_per_week) == 0:
            print(f'\033[38;2;10;235;190mNo Birthday this week.\033[0m')
            return None
        users = defaultdict(list)
        for item in birthday_per_week:
            if item[2] == 1:
                users['Monday'].append(item[0])
            if item[2] == 2:
                users['Tuesday'].append(item[0])   
            if item[2] == 3:
                users['Wednesday'].append(item[0])
            if item[2] == 4:
                users['Thursday'].append(item[0])
            if item[2] == 5:
                users['Friday'].append(item[0])
            if item[2] == 6:
                users['Satturday'].append(item[0])
            if item[2] == 7:
                users['Sunday'].append(item[0])
        return {key: value for key, value in users.items() if value} 

    # List of birthdays this week
    def get_birthdays_per_week_menu(self):
        table = Table(title="Birthdays information", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Date of birth", style="bold green", justify="center")
        table.add_column("Day of the week", style="red", justify="center")
        table.add_column("Names", style="bold blue", justify="center")
        if not self.phone_book:
            print(f'\033[91mNo contacts.\033[0m')
            return
        birthdays = self.get_birthdays_per_week()
        if birthdays:
            for k, v in birthdays.items():
                v_1 = ', '.join(p for p in v)
                table.add_row(k, v_1)
            self.console.print(table)


    # виводити список контактів, у яких день народження через задану кількість днів від поточної дати
    def birthday_in_given_days(self, value):
        date_today = date.today()
        date_value = date_today + timedelta(days=value)         
        contact_birth = []
        for n, rec in self.phone_book.data.items():
            name = n
            if rec.birthday:
                birth = rec.birthday.value.replace(year=date_today.year)
                if birth < date_today - timedelta(days=1):
                    birth = birth.replace(year=date_today.year+1)
                if date_today <=  birth <= date_value:
                    contact_birth.append(f'{name}; {rec.birthday.value}; {rec.days_to_birthday()}')

        if len(contact_birth) == 0:
            print(f'\033[38;2;10;235;190mNo Birthday during this period.\033[0m')
            return None
        
        return contact_birth

    # Displaying birthdays for a number of days
    def birthday_in_given_days_menu(self):
        table = Table(title="Birthdays information", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Name", style="red", justify="center")
        table.add_column("Date of birth", style="bold blue", justify="center")
        table.add_column("Day to birthday", style="bold blue", justify="center")
        if not self.phone_book:
            print(f'\033[91mNo contacts.\033[0m')
            return
        while True:
            print(f'\033[38;2;10;235;190mEnter the required number of days (no more than one year) or press ENTER to skip.\033[0m')
            item_number = input('\033[38;2;10;235;190mEnter the number=> \033[0m')
            if item_number:
                if item_number.isdigit() and item_number > '365':
                    # Введено число
                    item_number = int(item_number)
                    days_birth = self.birthday_in_given_days(item_number)
                    if days_birth:
                        for elem in days_birth:
                            item = elem.split(';')
                            table.add_row(item[0], item[1], item[2])
                        self.console.print(table)
                        return
                elif item_number.isalpha():
                    # Введены буквы
                    print(f'\033[91mYou entered letters: {item_number}\033[0m')
                else:
                    # Введены буквы
                    print(f'\033[91mYou entered a mumber greater than one year: {item_number}\033[0m')

            return


# меню для работы с нотатками
class NotesAssistant(Assistant):
    def __init__(self):
        super().__init__()
        self.colors = 'cyan'
        self.notes = []
        self.file = 'Save_Notes.bin'
        self.read_from_file()
        
    def handler(self):
        if os.path.isfile(self.file):  # запуск файла с сохранеными контактами!!!
            self.read_from_file()
        exit_menu = ExitAssistant()
        commands_text = "How can I assist you? Please select an option:"
        commands_menu = {
            'ADD NOTE': [self.note_add_menu, "cyan"],
            'EDIT NOTE': [self.note_charge_menu, "blue"],
            'DELETE NOTE': [self.note_delete_menu, "red"],
            'SEARCH NOTE': [self.note_search_menu, "blue"],
            'SHOW ALL NOTE': [self.note_show_menu, "blue"],
            'RETURN TO MAIN MENU': [Assistant, ""],
            'EXIT': [exit_menu.handler, ""],
        }
        self.table_menu(commands_menu, commands_text)
        result = self.handler_user_input(commands_menu)
        if result in commands_menu:
            commands_menu[result][0]()
            return
        
    def table_print_note(self):
        table = Table(title="Note Information", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Content", style="bold green", justify="center")
        table.add_column("Tags", style="bold blue", justify="center")
    
        table.add_row(
            str(self.notes.content),
            str(self.note.tags),
          )
        return table

    def add_note(self, content, tags=None):
        if tags is None:
            tags = []
        note = Note(content, tags)
        self.notes.append(note)
        
    def note_add_menu(self):
        content = input('Enter your text for the note: ')
        tags = input('Enter tags separated by commas (or press Enter if no tags): ').split(',')
        self.add_note(content, tags)
        self.write_to_file()

    def search_notes_by_tag(self, tag):
        return [note for note in self.notes if tag in note.tags]
            
    def display_all_notes(self):
        table = Table(title="Note Information", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Content", style="bold blue", justify="center")
        table.add_column("Tags", style="bold blue", justify="center")
        if not self.notes:
            print('\033[91mList empty.\033[0m')
        else:
            for i, note in enumerate(self.notes, 1):
                table.add_row(str(note.content), str(note.tags))
            self.console.print(table)

    def edit_note_content(self, tag, new_content):
        for note in self.notes:
            if tag not in note.tags:
                print('\033[91mInvalid note index.\033[0m')
            if tag in note.tags:
                note.content = new_content
                print(f'\033[92mNote update successfully.\033[0m')

    def search_and_sort_notes(self, keyword):
        found_notes = [note for note in self.notes if keyword in note.tags]
        sorted_notes = sorted(found_notes, key=lambda x: x.tags)
        return sorted_notes

    def delete_note_by_index(self, tag):
        initial_len = len(self.notes)
        self.notes = [note for note in self.notes if tag not in note.tags]
        if len(self.notes) == initial_len:
            print(f'\033[91mNo note found with tag "{tag}".\033[0m')
        else:
            print(f'\033[92mNote with tag "{tag}" deleted successfully.\033[0m')

    def note_charge_menu(self):
        index = input('Enter tag of the note to edit: ')
        new_content = input('Enter new text for the note: ')
        self.edit_note_content(index, new_content)
        self.write_to_file()

    def note_delete_menu(self):
        index = input('Enter tag of the note to delete: ')
        self.delete_note_by_index(index)
        self.write_to_file()

    def note_search_menu(self):
        table = Table(title="Note Information", style="cyan", title_style="bold magenta", width = 100)
        table.add_column("Content", style="bold blue", justify="center")
        table.add_column("Tags", style="bold blue", justify="center")
        tag_to_search = input('Enter tag for search and sort: ')
        sorted_notes = self.search_and_sort_notes(tag_to_search)
        if sorted_notes:
            print(f'\033[92mFound and Sorted Notes with Tag "{tag_to_search}":\033[0m')
            for note in sorted_notes:
                table.add_row(str(note.content), str(note.tags))
            self.console.print(table)
        else:
            print('\033[91mNothing to sort!\033[0m')

    def note_show_menu(self):
        self.display_all_notes()
        
    def write_to_file(self):
        with open(self.file, 'wb') as file:
            pickle.dump(self.notes, file)

    def read_from_file(self):
        try:
            with open(self.file, 'rb') as file:
                self.notes = pickle.load(file)
            return self.notes
        except FileNotFoundError:
            pass

    def exit(self):
        self.write_to_file()
        return True


# меню для работы по выходу из программы    
class ExitAssistant(Assistant):
    def __init__(self):
        super().__init__()
        # self.colors = 'cyan'
          
    def handler(self):
        ContactAssistant.exit
        NotesAssistant.exit
        print(colored('Good bye!', self.colors))
        exit()


if __name__ == "__main__":
    pass
        





   

    

   
            
    
