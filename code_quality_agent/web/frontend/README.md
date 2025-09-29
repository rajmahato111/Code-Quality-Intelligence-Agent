# Code Quality Intelligence Agent - Frontend

A modern React-based web interface for the Code Quality Intelligence Agent, providing comprehensive code analysis visualization and interactive Q&A capabilities.

## Features

- **Repository Analysis**: Analyze GitHub repositories with real-time progress tracking
- **Interactive Results**: Browse and filter code quality issues with detailed explanations
- **AI Q&A**: Ask natural language questions about your codebase and get intelligent answers
- **Real-time Updates**: Live progress tracking during analysis with WebSocket support
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Modern UI**: Clean, intuitive interface built with Tailwind CSS

## Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **TanStack Query** for data fetching and caching
- **Tailwind CSS** for styling
- **React Hook Form** for form management
- **Recharts** for data visualization
- **Prism** for syntax highlighting
- **Vitest** for testing

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API server running (see main project README)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:
```env
VITE_API_BASE_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main application layout
│   ├── ProgressTracker.tsx  # Real-time progress display
│   ├── IssueCard.tsx   # Issue display component
│   ├── MetricsOverview.tsx  # Analysis metrics dashboard
│   └── CodeSnippet.tsx # Syntax-highlighted code display
├── pages/              # Page components
│   ├── HomePage.tsx    # Landing page
│   ├── AnalysisPage.tsx # Repository analysis form
│   ├── ResultsPage.tsx # Analysis results display
│   ├── QAPage.tsx      # Interactive Q&A interface
│   └── NotFoundPage.tsx # 404 error page
├── services/           # API integration
│   └── api.ts          # API client and types
├── test/               # Test utilities and setup
│   ├── setup.ts        # Test environment setup
│   └── e2e/            # End-to-end tests
└── App.tsx             # Main application component
```

## Key Components

### ProgressTracker
Real-time analysis progress display with:
- Progress percentage and current step
- Files processed counter
- Issues found counter
- Estimated time remaining
- Live status updates

### IssueCard
Interactive issue display featuring:
- Severity and category indicators
- Code location information
- Confidence scores
- Quick fix suggestions
- Expandable details

### MetricsOverview
Comprehensive analysis dashboard showing:
- Overall quality score
- Issue breakdown by severity and category
- Repository information
- Analysis timing and statistics

### QAPage
Interactive Q&A interface with:
- Natural language question input
- Contextual answers based on analysis results
- Conversation history
- Suggested questions
- File-specific queries

## API Integration

The frontend communicates with the backend API through a centralized service layer (`services/api.ts`) that provides:

- Type-safe API calls with TypeScript interfaces
- Automatic authentication handling
- Error handling and retry logic
- Request/response interceptors
- Real-time progress polling

## Testing

### Unit Tests
```bash
npm run test
```

### Watch Mode
```bash
npm run test:watch
```

### Test Coverage
```bash
npm run test -- --coverage
```

### End-to-End Tests
```bash
npm run test:e2e
```

## Development

### Code Style
The project uses ESLint and Prettier for code formatting:
```bash
npm run lint
npm run format
```

### Type Checking
```bash
npm run type-check
```

### Hot Reload
The development server supports hot module replacement for fast development cycles.

## Deployment

### Docker
```bash
# Build the image
docker build -t code-quality-frontend .

# Run the container
docker run -p 3000:80 code-quality-frontend
```

### Static Hosting
The built application can be deployed to any static hosting service:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

## Configuration

### Environment Variables
- `VITE_API_BASE_URL`: Backend API base URL
- `VITE_WS_URL`: WebSocket URL for real-time updates (optional)
- `VITE_SENTRY_DSN`: Sentry DSN for error tracking (optional)

### Proxy Configuration
The development server proxies API requests to avoid CORS issues:
```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

## Performance Optimizations

- **Code Splitting**: Automatic route-based code splitting
- **Lazy Loading**: Components loaded on demand
- **Query Caching**: Intelligent data caching with TanStack Query
- **Image Optimization**: Optimized image loading and caching
- **Bundle Analysis**: Built-in bundle size analysis

## Accessibility

The application follows WCAG 2.1 guidelines:
- Semantic HTML structure
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes
- Focus management

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.