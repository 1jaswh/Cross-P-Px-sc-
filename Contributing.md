# Contributing to Cross-P (Px)

Thank you for your interest in contributing to **Cross-P (Px)**! We welcome contributions from developers, designers, and testers to improve the project.

---

## How to Contribute

### 1. Fork the Repository

Click the "Fork" button on GitHub to create your own copy of the repository.

### 2. Clone Your Fork

```bash
git clone https://github.com/your-username/Cross-P-Px.git
cd Cross-P-Px
```

### 3. Create a Branch

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

* Write clear, well-documented code.
* Follow the existing project structure and coding conventions.
* Update or add unit tests in the `tests/` folder.
* Ensure Streamlit pages remain functional and visually consistent.

### 5. Test Your Changes

```bash
pytest tests/
```

* All tests should pass before submitting a pull request.
* Verify that WebSocket updates and API endpoints work correctly.

### 6. Commit and Push

```bash
git add .
git commit -m "Describe your feature or fix"
git push origin feature/your-feature-name
```

### 7. Open a Pull Request

* Go to your fork on GitHub.
* Click "Compare & pull request".
* Provide a clear description of your changes and why they are necessary.

---

## Guidelines

* Be respectful and constructive when giving feedback.
* Keep pull requests focused on a single feature or bug fix.
* Include screenshots if you change the UI.
* Reference any relevant issues (e.g., `Fixes #123`).

---

## Reporting Bugs

If you encounter a bug:

1. Search existing issues to see if it has already been reported.
2. If not, open a new issue with:

   * Steps to reproduce
   * Expected vs. actual behavior
   * Screenshots or logs if applicable

---

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
