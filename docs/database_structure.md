# Bible Database Structure

Source: [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases)

## Overview

The `data/KJV.db` file is an SQLite database containing the King James Version (KJV) of the Bible, sourced from the [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases) project. The database also includes cross-reference data.

## Tables

The schema follows the convention used across all translations in the scrollmapper project.

### `KJV_books`
Lists all books in the KJV translation.

| Column | Type         | Description                      |
|--------|--------------|----------------------------------|
| `id`   | int (PK)     | Unique identifier for each book  |
| `name` | varchar(255) | The name of the book             |

### `KJV_verses`
Contains all verses in the KJV translation.

| Column    | Type     | Description                                                  |
|-----------|----------|--------------------------------------------------------------|
| `id`      | int (PK) | Unique identifier for each verse                             |
| `book_id` | int      | Foreign key referencing `KJV_books.id`                       |
| `chapter` | int      | The chapter number                                           |
| `verse`   | int      | The verse number                                             |
| `text`    | text     | The text of the verse                                        |

### `translations`
Metadata about the Bible translation(s) in the database.

| Column        | Type         | Description                          |
|---------------|--------------|--------------------------------------|
| `translation` | varchar(255) | Abbreviation of the translation (PK) |
| `title`       | varchar(255) | Full title of the translation        |
| `license`     | text         | License information                  |

## Database Stats

- **Translation**: KJV (King James Version, 1769) with Strong's Numbers and Morphology
- **Total verses**: 31,102
- **Books**: 66 (Old and New Testament)
- **License**: GPL

## Example Queries

### Retrieve all books
```sql
SELECT * FROM KJV_books;
```

### Get the first chapter of Genesis
```sql
SELECT * FROM KJV_verses
WHERE book_id = (SELECT id FROM KJV_books WHERE name = 'Genesis')
AND chapter = 1;
```

### Search for a verse by text
```sql
SELECT b.name, v.chapter, v.verse, v.text
FROM KJV_verses v
JOIN KJV_books b ON v.book_id = b.id
WHERE v.text LIKE '%In the beginning%';
```

### Get the entire book of John
```sql
SELECT b.name, v.chapter, v.verse, v.text
FROM KJV_verses v
JOIN KJV_books b ON v.book_id = b.id
WHERE b.name = 'John'
ORDER BY v.chapter, v.verse;
```

## Source Repository Documentation

The full documentation for the scrollmapper/bible_databases project is available at:
https://github.com/scrollmapper/bible_databases/blob/2025/docs/README.md

Key documentation sections:
1. [Introduction](https://github.com/scrollmapper/bible_databases/blob/2025/docs/0_introduction.md)
2. [Project Structure](https://github.com/scrollmapper/bible_databases/blob/2025/docs/1_project_layout.md)
3. [Scripting](https://github.com/scrollmapper/bible_databases/blob/2025/docs/2_scripting.md)
4. [SQL: Schemas and Queries](https://github.com/scrollmapper/bible_databases/blob/2025/docs/3_sql.md)
5. [Adding texts from ESword](https://github.com/scrollmapper/bible_databases/blob/2025/docs/4_adding_texts.md)
