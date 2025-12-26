# Sistema Legislativo

Plataforma DJANGO para tentar substituir a planilha por uma interface gráfica web

* Criar o ambiente virtual com PyEnv

      pyenv virtualenv 3.14 sistema_legislativo

* Atualizar o Pip

      python -m pip install --upgrade pip

* Instalar o Django

      pip install django

* Criar o projeto Django

      django-admin startproject meuprojeto

* Criar um aplicativo (app)

      cd meuprojeto
      python manage.py startapp minha_app

* Criar o super usuário do django admin

      python manage.py createsuperuser

* Rodar o Servidor de Desenvolvimento

      python manage.py runserver

* Requerimentos

  * Salvando os Requerimentos da aplicação

        pip freeze > requirements.txt

  * Carregando os requerimentos

        pip install -r requirements.txt










