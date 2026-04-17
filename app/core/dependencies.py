from fastapi import Request


def get_inscription_service(request: Request):
    """
    Retorna la instancia del servicio de inscripción almacenada en app.state.
    """
    service = request.app.state.wsn_inscription_service
    if service is None:
        raise RuntimeError("El servicio de inscripción no está disponible")
    return service


def get_padron_service(request: Request):
    """
    Retorna la instancia del servicio de padrón almacenada en app.state.
    """
    service = request.app.state.wsn_padron_service
    if service is None:
        raise RuntimeError("El servicio de padrón no está disponible")
    return service
