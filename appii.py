from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from model import *

api=Api()

class SectionResource(Resource):
    def get(self, section_id):
        section = Section.query.get(section_id)
        if section:
            return {
                'id': section.id,
                'name': section.name,
                'description': section.description,
                'date_created': section.date_created.isoformat() if section.date_created else None
            }
        else:
            return {'message': 'Section not found'}, 404

    def put(self, section_id):
        section = Section.query.get(section_id)
        if section:
            data = request.get_json()
            section.name = data.get('name', section.name)
            section.description = data.get('description', section.description)
            db.session.commit()
            return {
                'id': section.id,
                'name': section.name,
                'description': section.description,
                'date_created': section.date_created.isoformat() if section.date_created else None
            }
        else:
            return {'message': 'Section not found'}, 404
        
    def post(self):
        data = request.get_json()
        section = Section(
            name=data['name'],
            description=data['description'],
            date_created=datetime.now()
        )
        db.session.add(section)
        db.session.commit()
        return {
            'id': section.id,
            'name': section.name,
            'description': section.description,
            'date_created': section.date_created.isoformat() if section.date_created else None
        }

    def delete(self, section_id):
        section = Section.query.get(section_id)
        if section:
            db.session.delete(section)
            db.session.commit()
            return {'message': 'Section deleted successfully'}
        else:
            return {'message': 'Section not found'}, 404
        
class EBookResource(Resource):
    def get(self, ebook_id):
        ebook = EBook.query.get(ebook_id)
        if ebook:
            return {
                'id': ebook.id,
                'name': ebook.name,
                'image': ebook.image,
                'pdf': ebook.pdf,
                'release_date': ebook.release_date.isoformat(),
                'author_name': ebook.author_name,
                'total_pages': ebook.total_pages,
                'return_date': ebook.return_date.isoformat() if ebook.return_date else None,
                'return_date_expected': ebook.return_date_expected.isoformat() if ebook.return_date_expected else None,
                'content': ebook.content,
                'section_id': ebook.section_id,
                'section_name': ebook.section_name,
                'price': ebook.price
            }
        else:
            return {'message': 'EBook not found'}, 404

    def put(self, ebook_id):
        ebook = EBook.query.get(ebook_id)
        if ebook:
            data = request.get_json()
            ebook.name = data.get('name', ebook.name)
            ebook.image = data.get('image', ebook.image)
            ebook.pdf = data.get('pdf', ebook.pdf)
            ebook.release_date = datetime.strptime(data['release_date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            ebook.author_name = data.get('author_name', ebook.author_name)
            ebook.total_pages = data.get('total_pages', ebook.total_pages)
            ebook.return_date = datetime.strptime(data['return_date'], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('return_date') else None
            ebook.return_date_expected = datetime.strptime(data['return_date_expected'], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('return_date_expected') else None
            ebook.content = data.get('content', ebook.content)
            ebook.section_id = data.get('section_id', ebook.section_id)
            ebook.section_name = data.get('section_name', ebook.section_name)
            ebook.price = data.get('price', ebook.price)
            db.session.commit()
            return {
                'id': ebook.id,
                'name': ebook.name,
                'image': ebook.image,
                'pdf': ebook.pdf,
                'release_date': ebook.release_date.isoformat(),
                'author_name': ebook.author_name,
                'total_pages': ebook.total_pages,
                'return_date': ebook.return_date.isoformat() if ebook.return_date else None,
                'return_date_expected': ebook.return_date_expected.isoformat() if ebook.return_date_expected else None,
                'content': ebook.content,
                'section_id': ebook.section_id,
                'section_name': ebook.section_name,
                'price': ebook.price
            }
        else:
            return {'message': 'EBook not found'}, 404

    def delete(self, ebook_id):
        ebook = EBook.query.get(ebook_id)
        if ebook:
            db.session.delete(ebook)
            db.session.commit()
            return {'message': 'EBook deleted successfully'}
        else:
            return {'message': 'EBook not found'}, 404

    def post(self):
        data = request.get_json()
        ebook = EBook(
            name=data['name'],
            image=data['image'],
            pdf=data['pdf'],
            release_date=datetime.strptime(data['release_date'], '%Y-%m-%dT%H:%M:%S.%fZ'),
            author_name=data['author_name'],
            total_pages=data['total_pages'],
            return_date=datetime.strptime(data['return_date'], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('return_date') else None,
            return_date_expected=datetime.strptime(data['return_date_expected'], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('return_date_expected') else None,
            content=data['content'],
            section_id=data['section_id'],
            section_name=data['section_name'],
            price=data['price']
        )
        db.session.add(ebook)
        db.session.commit()
        return {
            'id': ebook.id,
            'name': ebook.name,
            'image': ebook.image,
            'pdf': ebook.pdf,
            'release_date': ebook.release_date.isoformat(),
            'author_name': ebook.author_name,
            'total_pages': ebook.total_pages,
            'return_date': ebook.return_date.isoformat() if ebook.return_date else None,
            'return_date_expected': ebook.return_date_expected.isoformat() if ebook.return_date_expected else None,
            'content': ebook.content,
            'section_id': ebook.section_id,
            'section_name': ebook.section_name,
            'price': ebook.price
        }

class UserResource(Resource):
    def get(self, user_id):
        user = User.query.get(user_id)
        if user:
            return {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'password': user.password,
                'role': user.role
            }
        else:
            return {'message': 'User not found'}, 404

    def put(self, user_id):
        user = User.query.get(user_id)
        if user:
            data = request.get_json()
            user.name = data.get('name', user.name)
            user.email = data.get('email', user.email)
            user.password = data.get('password', user.password)
            user.role = data.get('role', user.role)
            db.session.commit()
            return {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'password': user.password,
                'role': user.role
            }
        else:
            return {'message': 'User not found'}, 404

    def delete(self, user_id):
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return {'message': 'User deleted successfully'}
        else:
            return {'message': 'User not found'}, 404

    def post(self):
        data = request.get_json()
        user = User(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            role=data['role']
        )
        db.session.add(user)
        db.session.commit()
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password': user.password,
            'role': user.role
        }

api.add_resource(SectionResource, '/api/sections/<int:section_id>','/api/add_sections', '/api/update_sections/<int:section_id>', '/api/delete_sections/<int:section_id>')
api.add_resource(EBookResource, '/api/ebooks/<int:ebook_id>','/api/add_ebooks', '/api/update_ebooks/<int:ebook_id>', '/api/delete_ebooks/<int:ebook_id>')
