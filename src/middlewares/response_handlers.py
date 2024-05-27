import jose
from jose import jwt
from typing import Any, Annotated

from fastapi import Request, Response, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from frontend.model import UserFrontendModel
from middlewares.registrator import register_modder
from frontend.routes import templates
from auth.service import auth as auth_service
from database import sessionmanager
from settings import settings


async def get_user_from_request(
        request: Request
) -> Any:
    user = None
    access_token = request.cookies.get('access_token')

    if access_token:
        async with sessionmanager.session() as db:
            user_orm = await auth_service.get_access_user(access_token,
                                                          db)
            user = UserFrontendModel.from_orm(user_orm)

    return user


@register_modder('get_my_profile')
async def html_get_my_profile(request: Request,
                              response: Response,
                              data: dict) -> Any:
    """HTMX transformer for get_my_profile response

            Args:
                response (Response): response object to handle
                data (dict): mapped response data

            Returns:
                HTML data for htmx
    """
    print("Response handler for get_my_profile", data)

    return response


@register_modder('auth_login')
async def html_auth_login(request: Request,
                          response: Response,
                          data: dict) -> Any:
    """HTMX transformer for auth_login response

            Args:
                response (Response): response object to handle
                data (dict): mapped response data

            Returns:
                HTML data for htmx
    """
    status_code = response.status_code
    if status_code >= 400:
        error_message = data.get('detail').get('msg')
        return templates.TemplateResponse(
            'auth/login.html', {'request': request,
                                'error': error_message}
        )
    access_token = data.get('access_token')
    try:
        access_payload = jwt.decode(token=access_token,
                                    key=settings.secret_256,
                                    algorithms=[settings.access_algorithm])
    except jose.exceptions.JWTError:
        return templates.TemplateResponse(
            'auth/login.html', {'request': request,
                                'error': 'Invalid credentials'}
        )

    refresh_token = data.get('refresh_token')
    try:
        refresh_payload = jwt.decode(token=refresh_token,
                                    key=settings.secret_512,
                                    algorithms=[settings.refresh_algorithm])
    except jose.exceptions.JWTError:
        return templates.TemplateResponse(
            'auth/login.html', {'request': request,
                                'error': 'Invalid credentials',
                                'user': None}
        )

    response = RedirectResponse('/',
                                status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key='access_token',
                        value=access_token,
                        httponly=True,
                        expires=access_payload.get('exp'))
    response.set_cookie(key='refresh_token',
                        value=refresh_token,
                        httponly=True,
                        expires=refresh_payload.get('exp'))
    return response


@register_modder('auth_logout')
async def html_auth_logout(request: Request,
                           response: Response,
                           data: dict) -> Any:
    """HTMX transformer for auth_logout response

            Args:
                request (Request): request object to handle
                response (Response): response object to handle
                data (dict): mapped response data

            Returns:
                HTML data for htmx
    """
    response = RedirectResponse('/',
                                status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


@register_modder('get_photos')
async def html_get_photos(request: Request,
                          response: Response,
                          data: dict) -> Any:
    """HTMX transformer for get_photos response

            Args:
                request (Request): request onject to handle
                response (Response): response object to handle
                data (dict): mapped response data

            Returns:
                HTML data for htmx
    """
    if len(data) == 0:
        return templates.TemplateResponse('photo/photo_list.html',
                                          {'request': request,
                                           'photo_list': None})
    return templates.TemplateResponse('photo/photo_list.html',
                                      {'request': request,
                                       'photo_list': data})


@register_modder('create_photo')
async def html_create_photo(request: Request,
                            response: Response,
                            data: dict) -> Any:
    """HTMX transformer for create_photo response

            Args:
                request (Request): request onject to handle
                response (Response): response object to handle
                data (dict): mapped response data

            Returns:
                HTML data for htmx
    """
    if response.status_code >= 400:
        error_message = data.get('detail').get('msg')
        return templates.TemplateResponse(
            'photo/photo_add.html', {'request': request,
                                     'error': error_message}
        )
    return RedirectResponse('/',
                            status_code=status.HTTP_303_SEE_OTHER)


@register_modder("get_photo_id")
async def html_get_photo_id(
        request: Request,
        response: Response,
        data: dict,
) -> Any:
    user = await get_user_from_request(request)
    if response.status_code >= 400:
        error_message = data.get('detail').get('msg')
        return templates.TemplateResponse(
            'photo/detailed_page.html',
            {'request': request,
             'error': error_message,
             'user': user}
        )
    return templates.TemplateResponse(
        "photo/detailed_page.html",
        {'request': request,
         'photo': data,
         'error': None,
         'user': user}
    )
