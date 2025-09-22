# Contributing to Qatar University Chatbot

Thank you for your interest in contributing to the Qatar University Chatbot! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Azure subscription (for testing with real services)
- Basic knowledge of Python, Streamlit, and Azure services

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/Qatar-University-Chatbot.git
   cd Qatar-University-Chatbot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov flake8 black  # Development dependencies
   ```

4. **Setup Environment**
   ```bash
   cp env.example .env
   # Edit .env with your Azure service credentials
   ```

## 📝 Development Guidelines

### Code Style

- Follow **PEP 8** Python style guide
- Use **Black** for code formatting: `black .`
- Maximum line length: 127 characters
- Use type hints where possible
- Add docstrings to all functions and classes

### Commit Messages

Use clear, descriptive commit messages:
```
feat: add document type filtering to search
fix: resolve PDF processing error for large files
docs: update README with new deployment options
test: add unit tests for document processor
```

### Testing

- Write unit tests for new features
- Ensure all tests pass: `pytest`
- Aim for >80% code coverage
- Test with different document types and sizes

## 🎯 Areas for Contribution

### High Priority
- **Performance Optimization**: Improve search speed and response times
- **Error Handling**: Better error messages and recovery
- **Documentation**: Improve setup guides and API docs
- **Testing**: Add comprehensive test coverage

### Medium Priority
- **UI/UX Improvements**: Enhance Streamlit interface
- **Multi-language Support**: Add Arabic language support
- **Voice Interface**: Integrate speech-to-text/text-to-speech
- **Analytics**: Add usage analytics and insights

### Low Priority
- **Mobile App**: Create mobile application
- **Integration**: Connect with university systems
- **Advanced Features**: Add more AI capabilities

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Details**
   - Python version
   - Operating system
   - Azure service versions

2. **Steps to Reproduce**
   - Clear, numbered steps
   - Sample documents (if applicable)
   - Expected vs actual behavior

3. **Error Information**
   - Full error messages
   - Stack traces
   - Log files (if available)

## 💡 Feature Requests

For new features:

1. **Check Existing Issues**: Search for similar requests
2. **Provide Context**: Explain the use case and benefits
3. **Mockups**: Include UI mockups if applicable
4. **Implementation Ideas**: Suggest technical approach

## 🔧 Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Thoroughly**
   ```bash
   pytest
   flake8 .
   black --check .
   ```

4. **Submit Pull Request**
   - Clear title and description
   - Reference related issues
   - Include screenshots for UI changes

## 📋 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## 🔒 Security

- **Never commit secrets**: API keys, passwords, or sensitive data
- **Use environment variables**: For all configuration
- **Report vulnerabilities**: Email security@qu.edu.qa
- **Follow secure coding**: Validate inputs, handle errors safely

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: For security issues or private matters

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Qatar University Chatbot! 🎓
