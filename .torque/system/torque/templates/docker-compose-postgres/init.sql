{%- for user, password in users.items() | sort %}
    {%- if user != 'postgres' -%}
        CREATE USER {{user}} WITH CREATEDB CREATEROLE PASSWORD '{{password}}';
    {% endif -%}
{%- endfor %}

{% for database, users in databases.items() | sort %}
    {%- if database != 'postgres' -%}
        CREATE DATABASE {{database}};
    {% endif -%}
{%- endfor %}

{% for database, users in databases.items() | sort -%}
    {% for user in users | sort -%}
        {%- if user != 'postgres' -%}
            GRANT ALL PRIVILEGES ON DATABASE {{database}} TO {{user}};
        {% endif -%}
    {%- endfor -%}
{%- endfor -%}
