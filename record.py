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


class Field:
    def __init__(self, value):
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    def __str__(self):
        return str(self.__value)


class Name(Field):
    pass

class Address(Field):
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: str):
        self.__value = value

    def __str__(self):
        return str(self.__value)


class Email(Field):
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: str):
        pattern = r"^[a-zA-Z0-9._]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if (bool(re.search(pattern, value))) is False:
            raise ValueError('\033[91mInvalid email format.\033[0m')
        self.__value = value

    def __str__(self):
        return str(self.__value)


class Birthday(Field):
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: str):
        try:
            self.__value = datetime.strptime(value, '%Y.%m.%d').date()
        except ValueError:
            raise ValueError('\033[91mInvalid date format. Correct format: YYYY.MM.DD\033[0m')

    def __str__(self):
        return self.__value.strftime('%Y.%m.%d')
    


class Phone(Field):
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if len(value) != 10 or not value.isdigit():
            raise ValueError('\033[91mThe phone number should be digits only and have 10 symbols.\033[0m')
        self.__value = value

    def __str__(self):
        return(str(self.__value))


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
        self.email = None
        self.address = None

    def add_phone(self, value: str):
        phone = Phone(value)
        self.phones.append(phone)

    def add_email(self, value: str):
        self.email = Email(value)

    def add_address(self, value: str):
        self.address = Address(value)

    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def remove_phone(self, phone: str):
        for item in self.phones:
            if item.value == phone:
                self.phones.remove(item)
                return f'The phone number: {phone} has been deleted.'
        return f'The phone number {phone} not found.'

    def edit_phone(self, old_phone: str, new_phone: str):
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone
                return f'Phones: {"; ".join(p.value for p in self.phones)}'
        return None

    def find_phone(self, phone: str):
        for item in self.phones:
            if item.value == phone:
                return item
        return None

    #  показывает сколько дней до дня рождения
    def days_to_birthday(self):
        if self.birthday is None:
            return None
        date_today = date.today()
        birthday_date = self.birthday.value.replace(year=date_today.year)
        if date_today == birthday_date:
            return 'Birthday today'
        if birthday_date <= date_today - timedelta(days=1):
            birthday_date = birthday_date.replace(year=date_today.year + 1)
        day_to_birthday = (birthday_date - date_today).days
        return day_to_birthday

    def __str__(self):
        
        return f'{self.name.value}, {"; ".join(p.value for p in self.phones)}, {self.birthday}, {self.email}, {self.address}, {self.days_to_birthday()}'

class AddressBook(UserDict):
    def __init__(self):
        super().__init__()
        self.file = 'Phone_Book.bin'

    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str):
        if name in self.data:
            return self.data[name]
        return None

    def search(self, value: str):
        if len(value) < 3:
            return '\033[91mYou need at least 3 letters to search by name or 3 didgit to search by phone number.\033[0m'
        result = ''
        for name, rec in self.data.items():
            if value.lower() in name.lower():
                result += f'{str(rec)}\n'
            for item in rec.phones:
                if value in item.value:
                    result += f'{str(rec)}'
        if len(result) != 0:
            return result
        else:
            return None

    def delete(self, name: str):
        if name in self.data:
            self.data.pop(name)
            return f'The contact {name} has been deleted.'
        else:
            return f'The contact {name} not found.'

    def iterator(self, item_number):
        counter = 0
        result = f'Contacts:\n'
        print(result)
        print(self.data)
        for item, record in self.data.items():
            result += f'{item}: {str(record)}\n'
            counter += 1
            print(counter)
            if counter >= item_number:
                yield result
                counter = 0
                result = ''
        print(result)
        yield result

    def write_to_file(self):
        with open(self.file, 'wb') as file:
            pickle.dump(self.data, file)

    def read_from_file(self):
        with open(self.file, 'rb') as file:
            self.data = pickle.load(file)
        return self.data

# класс по созданию нотаток
class Note:
    def __init__(self, content, tags=None):
        if tags is None:
            tags = []
        self.content = content
        self.tags = tags

class Controller(cmd.Cmd):
    def exit(self):
        self.book.dump()
        return True
