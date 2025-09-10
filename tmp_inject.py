from fastapi import Depends
from security import require_key
from la.routes import router as la_router
from la.compat import router as compat_router
from la.ui import router as ui_router

# Attach an API key requirement to each router
la_router.dependencies = (la_router.dependencies or []) + [Depends(require_key)]
compat_router.dependencies = (compat_router.dependencies or []) + [Depends(require_key)]
ui_router.dependencies = (ui_router.dependencies or []) + [Depends(require_key)]
