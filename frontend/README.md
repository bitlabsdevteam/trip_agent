# AI Chat Assistant Frontend

This is the frontend for the AI Chat Assistant application, built with [Next.js](https://nextjs.org) and designed to connect to a Flask backend API. The application provides a real-time streaming chat interface with conversation memory.

## Features

- Real-time token-by-token streaming responses
- Conversation memory that maintains context
- Responsive design for all devices
- Dark mode support
- Stop generation functionality
- Clear conversation history

## Tech Stack

- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- Server-Sent Events (SSE) for streaming

## Getting Started

### Prerequisites

- Node.js 18.17 or later
- npm or yarn
- Backend API running (Flask server on port 3000)

### Installation

1. Install dependencies:

```bash
npm install
# or
yarn install
```

2. Run the development server:

```bash
npm run dev
# or
yarn dev
```

3. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Environment Configuration

Create a `.env.local` file in the root directory with the following variables:

```
NEXT_PUBLIC_API_URL=http://localhost:3000/api/v1
```

Adjust the URL to match your backend API endpoint.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a custom font family.

## Project Structure

- `/src/app` - Next.js App Router pages
- `/src/components` - React components
- `/src/hooks` - Custom React hooks
- `/public` - Static assets

## API Proxy

The frontend includes an API proxy at `/api/chat` that forwards requests to the backend API. This helps avoid CORS issues and provides a cleaner interface for the frontend.

## Customization

- Update the theme colors in `tailwind.config.js`
- Modify the chat interface in `ChatContainer.tsx`
- Adjust the API endpoints in `api/chat/route.ts`

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new) from the creators of Next.js.

1. Push your code to a Git repository (GitHub, GitLab, BitBucket)
2. Import the project into Vercel
3. Vercel will detect Next.js automatically and use the optimal build settings
4. Add environment variables in the Vercel dashboard
5. Deploy

Check out the [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
