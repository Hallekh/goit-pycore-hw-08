import pickle
from collections import UserDict
from datetime import datetime, date

FILENAME = "addressbook.pkl"

# Функції серіалізації/десеріалізації з використанням pickle
def save_data(book, filename=FILENAME):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename=FILENAME):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Якщо файл не знайдено, повертаємо нову адресну книгу

# Базовий клас для полів
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# Клас для імені контакту
class Name(Field):
    pass

# Клас для номера телефону з валідацією (10 цифр)
class Phone(Field):
    def __init__(self, value):
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Номер телефону має складатися з 10 цифр.")
        super().__init__(value)

# Клас для зберігання дня народження; очікується формат DD.MM.YYYY
class Birthday(Field):
    def __init__(self, value):
        try:
            birthday_date = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(birthday_date)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

# Клас для запису контакту
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []       # Список об'єктів Phone
        self.birthday = None   # Об'єкт Birthday або None

    def add_phone(self, phone_str):
        phone_obj = Phone(phone_str)
        self.phones.append(phone_obj)

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)
        return f"День народження для {self.name.value} встановлено на {self.birthday.value.strftime('%d.%m.%Y')}."

    def days_to_birthday(self):
        if self.birthday is None:
            return None
        today = date.today()
        bday = self.birthday.value
        # Обчислюємо наступний день народження
        next_birthday = bday.replace(year=today.year)
        if next_birthday < today:
            next_birthday = bday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self):
        phones_str = ", ".join(phone.value for phone in self.phones) if self.phones else "Немає телефонів"
        birthday_str = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "Немає даних"
        return f"Ім'я: {self.name.value} | Телефони: {phones_str} | День народження: {birthday_str}"

# Клас для адресної книги (наслідується від UserDict)
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value.lower()] = record

    def find(self, name):
        return self.data.get(name.lower())

    def delete(self, name):
        if name.lower() in self.data:
            del self.data[name.lower()]
            return f"Запис {name} видалено."
        return "Запис не знайдено."

    def get_upcoming_birthdays(self, days=7):
        result = []
        today = date.today()
        for record in self.data.values():
            if record.birthday:
                next_bday = record.birthday.value.replace(year=today.year)
                if next_bday < today:
                    next_bday = record.birthday.value.replace(year=today.year + 1)
                delta = (next_bday - today).days
                if delta <= days:
                    result.append((record.name.value, delta))
        return result

# Декоратор для обробки помилок введення
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e) or "Invalid data provided."
        except IndexError:
            return "Enter the argument for the command"
        except KeyError:
            return "Contact not found."
    return inner

# Допоміжна функція для розбору введеного рядка
def parse_input(user_input: str):
    tokens = user_input.strip().split()
    if not tokens:
        return "", []
    command = tokens[0].lower()
    args = tokens[1:]
    return command, args

# Функції-обробники команд
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Контакт оновлено."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Контакт додано."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    return record.edit_phone(old_phone, new_phone)

@input_error
def phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.phones:
        return "; ".join(phone.value for phone in record.phones)
    else:
        return "Немає телефонів."

@input_error
def show_all(args, book: AddressBook):
    if not book.data:
        return "Адресна книга порожня."
    result = []
    for record in book.data.values():
        result.append(str(record))
    return "\n".join(result)

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday_str, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    return record.add_birthday(birthday_str)

@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday:
        return f"{record.name.value}'s birthday: {record.birthday.value.strftime('%d.%m.%Y')}"
    else:
        return "Дата народження не встановлена."

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays(days=7)
    if not upcoming:
        return "Немає контактів з днем народження протягом наступного тижня."
    result = []
    for name, days_left in upcoming:
        result.append(f"{name} через {days_left} днів")
    return "\n".join(result)

# Основна функція CLI‑бота
def main():
    book = load_data()  # Завантаження даних із файлу при старті
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)
        if command in ("exit", "close"):
            save_data(book)  # Збереження даних перед виходом
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(phone(args, book))
        elif command == "all":
            print(show_all(args, book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
