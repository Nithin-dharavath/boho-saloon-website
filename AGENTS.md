# Repository Guidelines

## Project Structure & Module Organization
`main.py` is the application entrypoint and defines the FastAPI app plus the `/` route. HTML templates live in `templates/` and are rendered through Jinja2. Frontend assets are split by type under `static/`:

- `static/css/style.css` for site styling and design tokens
- `static/js/script.js` for page interactions
- `static/images/` for landing-page imagery

Use `test/` for automated tests. The `database/` folder is currently empty, so keep new persistence code isolated there if database work is introduced.

## Build, Test, and Development Commands
- `python -m venv venv` creates the local virtual environment if needed.
- `venv\Scripts\activate` activates the environment on Windows PowerShell.
- `pip install -r requirements.txt` installs FastAPI, Uvicorn, and template dependencies.
- `python main.py` starts the app with reload enabled on `http://localhost:8000`.
- `uvicorn main:app --reload` is the preferred direct dev command when debugging server startup.

## Coding Style & Naming Conventions
Follow the existing formatting already in the repo:

- Python: 4-space indentation, `snake_case` for functions, clear route handler names like `index`.
- JavaScript and CSS: 2-space indentation, `camelCase` for variables, kebab-case for CSS classes such as `.navbar-links`.
- Reuse the CSS custom properties in `:root` before adding new color values or spacing constants.

No formatter or linter is configured yet, so keep changes small, consistent, and readable.

## Testing Guidelines
There is no committed automated suite yet. For backend changes, add tests under `test/` using `test_<feature>.py` naming and prefer `pytest` conventions if you introduce the framework. At minimum, manually verify the landing page, static asset loading, and any new route with `uvicorn main:app --reload` before opening a PR.

## Commit & Pull Request Guidelines
Recent commits use short, lowercase summaries such as `landing-page` and `index-updated`. Keep commit messages concise and descriptive, ideally in that same style.

Pull requests should include a brief summary, the commands used for verification, and screenshots for visual changes because this repository is primarily frontend-facing. Link the related issue or task when one exists.
