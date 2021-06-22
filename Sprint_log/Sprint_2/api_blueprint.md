Diners:
- Search
    - keyword
    - filter
    - sort
    - offset
    {'condition':
        {
            'keyword': [{'field': 'some_field', 'value': 'some_text'}],
            'sorter: {'field': 'some_field', 'filter': 'some_filter', value: value},
            'filter: {'field': 'some_field', 'sorter': 'some_sorter'},
            'offset': int
        }
    }
- List
    - offset
- Random
    - filter

Foods:
- Search
    - keyword
    - filter
    - sort
- Random
    - filter

Users:
- Register
    - email
    - password
    - name
- Login
    - email
    - password
- Collect
    - diner_id
    - section_id
    - subsection_id
    - item_title
- ReviewDiner
    - diner_id
    - review_datetime
    - review_content
    - review_rating
- ReviewFood
    - diner_id
    - section_id
    - subsection_id
    - item_title
    - review_datetime
    - review_content
    - review_rating

Recommendation:
- Diner
- Food