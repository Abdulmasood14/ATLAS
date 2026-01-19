# IMPLEMENTATION GUIDE - Remaining Frontend Components

This document lists all remaining frontend components that need to be implemented to complete the chatbot UI.

---

## ✅ **COMPLETED FILES**

### **Backend (100% Complete)**
- ✅ Database migrations (`backend/database/migrations.sql`)
- ✅ Pydantic models (`backend/models/schemas.py`)
- ✅ Database connection (`backend/database/connection.py`)
- ✅ RAG service wrapper (`backend/services/rag_service.py`)
- ✅ Chat API (`backend/api/chat.py`)
- ✅ Feedback API (`backend/api/feedback.py`)
- ✅ Upload API (`backend/api/upload.py`)
- ✅ Export API (`backend/api/export.py`)
- ✅ Main FastAPI app (`backend/main.py`)
- ✅ Requirements (`backend/requirements.txt`)

### **Frontend (Partial)**
- ✅ TypeScript types (`frontend/src/types/index.ts`)
- ✅ API client (`frontend/src/services/api.ts`)
- ✅ FeedbackButtons component (`frontend/src/components/FeedbackButtons.tsx`)
- ✅ Package.json, tsconfig.json, tailwind.config.js

---

## 🔨 **REMAINING FRONTEND COMPONENTS TO IMPLEMENT**

You can implement these components following the patterns established in the completed files.

### **1. Main App Pages**

#### **`frontend/src/app/page.tsx`** (Main Chat Page)
```typescript
// Main chat interface
// - Layout with sidebar and chat window
// - State management with useState/zustand
// - WebSocket connection
// - Message rendering
```

#### **`frontend/src/app/layout.tsx`** (Root Layout)
```typescript
// Root layout with:
// - HTML structure
// - Global providers (React Query, etc.)
// - Fonts
// - Metadata
```

#### **`frontend/src/app/globals.css`** (Global Styles)
```css
/* TailwindCSS base, components, utilities */
/* Custom animations */
/* Dark theme variables */
```

---

### **2. Core React Components**

#### **`frontend/src/components/ChatWindow.tsx`**
```typescript
/**
 * Main chat container
 * - Displays all messages
 * - Auto-scroll to bottom
 * - Typing indicator
 * - Loading states
 */
interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (query: string) => void;
}
```

#### **`frontend/src/components/MessageBubble.tsx`**
```typescript
/**
 * Individual message component
 * - User vs Assistant styling
 * - Source citations (collapsible)
 * - Feedback buttons (assistant only)
 * - Timestamp
 */
interface MessageBubbleProps {
  message: ChatMessage;
  sessionId: string;
}
```

#### **`frontend/src/components/InputBox.tsx`**
```typescript
/**
 * Query input component
 * - Auto-expanding textarea
 * - Send button
 * - File upload button
 * - Character counter (optional)
 */
interface InputBoxProps {
  onSubmit: (query: string) => void;
  isDisabled: boolean;
  placeholder?: string;
}
```

#### **`frontend/src/components/TypingIndicator.tsx`**
```typescript
/**
 * Animated typing indicator
 * - Three bouncing dots
 * - Shows while assistant is "thinking"
 */
```

#### **`frontend/src/components/UploadPanel.tsx`**
```typescript
/**
 * PDF upload interface
 * - Drag and drop zone
 * - File validation (PDF only, max 50MB)
 * - Progress bar
 * - Company metadata input
 */
interface UploadPanelProps {
  onUploadComplete: (companyId: string) => void;
}
```

#### **`frontend/src/components/Sidebar.tsx`**
```typescript
/**
 * Sidebar with:
 * - Company selector dropdown
 * - Session history
 * - Export button
 * - Clear conversation button
 */
interface SidebarProps {
  currentCompany: Company | null;
  onSelectCompany: (company: Company) => void;
}
```

#### **`frontend/src/components/CompanySelector.tsx`**
```typescript
/**
 * Dropdown to select company
 * - Fetches companies from API
 * - Shows chunk count
 * - Search/filter
 */
```

#### **`frontend/src/components/SourceCitation.tsx`**
```typescript
/**
 * Source citation component
 * - Collapsible list of sources
 * - Page numbers
 * - Note numbers
 * - Relevance score
 */
interface SourceCitationProps {
  sources: Source[];
}
```

---

### **3. Services**

#### **`frontend/src/services/websocket.ts`**
```typescript
/**
 * WebSocket client for real-time chat
 */
export class WebSocketClient {
  connect(sessionId: string): void;
  disconnect(): void;
  sendQuery(query: string, companyId: string): void;
  onMessage(callback: (data: any) => void): void;
  onTyping(callback: (isTyping: boolean) => void): void;
  onError(callback: (error: any) => void): void;
}
```

---

### **4. Custom Hooks**

#### **`frontend/src/hooks/useChat.ts`**
```typescript
/**
 * Chat state management hook
 */
export function useChat(sessionId: string) {
  return {
    messages: ChatMessage[],
    sendMessage: (query: string) => void,
    isLoading: boolean,
    error: string | null,
  };
}
```

#### **`frontend/src/hooks/useFeedback.ts`**
```typescript
/**
 * Feedback state management hook
 */
export function useFeedback() {
  return {
    submitFeedback: (messageId: number, score: number) => Promise<void>,
    isSubmitting: boolean,
  };
}
```

#### **`frontend/src/hooks/useUpload.ts`**
```typescript
/**
 * File upload hook with progress tracking
 */
export function useUpload() {
  return {
    uploadFile: (file: File, metadata: any) => Promise<void>,
    progress: number,
    isUploading: boolean,
    error: string | null,
  };
}
```

#### **`frontend/src/hooks/useSession.ts`**
```typescript
/**
 * Session management hook
 */
export function useSession() {
  return {
    createSession: (companyId: string, companyName: string) => Promise<ChatSession>,
    currentSession: ChatSession | null,
    sessions: ChatSession[],
  };
}
```

---

### **5. Utility Files**

#### **`frontend/src/lib/utils.ts`**
```typescript
/**
 * Utility functions
 */
export function formatTimestamp(date: string): string;
export function formatFileSize(bytes: number): string;
export function cn(...classes: string[]): string; // clsx helper
```

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Phase 1: Core UI** ⭐ Start Here
- [ ] Create `globals.css` with TailwindCSS setup
- [ ] Create `layout.tsx` (root layout)
- [ ] Create `page.tsx` (main page skeleton)
- [ ] Create `MessageBubble.tsx` (display messages)
- [ ] Create `InputBox.tsx` (query input)
- [ ] Create `ChatWindow.tsx` (message container)

### **Phase 2: Interactivity**
- [ ] Create `websocket.ts` (real-time connection)
- [ ] Create `useChat.ts` hook (state management)
- [ ] Connect `ChatWindow` to WebSocket
- [ ] Implement message sending
- [ ] Add typing indicator

### **Phase 3: Features**
- [ ] Create `Sidebar.tsx` (company selection)
- [ ] Create `CompanySelector.tsx` (dropdown)
- [ ] Create `UploadPanel.tsx` (PDF upload)
- [ ] Create `useUpload.ts` hook
- [ ] Implement export functionality

### **Phase 4: Polish**
- [ ] Add animations (Framer Motion)
- [ ] Responsive design (mobile)
- [ ] Error handling & toasts
- [ ] Loading states
- [ ] Dark theme refinement

---

## 🎨 **DESIGN REFERENCE**

### **Color Classes (TailwindCSS)**

```css
/* Backgrounds */
bg-background            /* #0F1729 - Deep navy */
bg-background-secondary  /* #1E293B - Charcoal */
bg-background-card       /* #1E2A3B - Card */

/* Primary (Teal/Cyan) */
bg-primary              /* #06B6D4 */
bg-primary-hover        /* #0891B2 */
text-primary

/* Accent (Gold) */
bg-accent               /* #F59E0B */
text-accent

/* Text */
text-text-primary       /* #FFFFFF */
text-text-secondary     /* #E2E8F0 */
text-text-muted         /* #94A3B8 */

/* Feedback Colors */
text-success            /* #10B981 - Good */
text-warning            /* #F59E0B - Medium */
text-error              /* #EF4444 - Bad */
```

### **Component Styling Patterns**

```tsx
// User Message (right-aligned, teal)
<div className="flex justify-end">
  <div className="bg-primary/20 text-text-primary px-4 py-2 rounded-2xl border border-primary/50">
    {message.content}
  </div>
</div>

// Assistant Message (left-aligned, card with shadow)
<div className="flex justify-start">
  <div className="bg-background-card text-text-secondary px-4 py-3 rounded-2xl shadow-glass border border-primary/10">
    {message.content}
  </div>
</div>

// Frosted Glass Effect
<div className="bg-background-card/80 backdrop-blur-md border border-primary/20 shadow-glass">
  ...
</div>
```

---

## 🔧 **QUICK START FOR FRONTEND DEVELOPMENT**

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Create `globals.css`**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-text-primary font-sans;
  }
}
```

3. **Create Basic `layout.tsx`**
```typescript
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
```

4. **Create Basic `page.tsx`**
```typescript
export default function Home() {
  return (
    <main className="h-screen bg-background">
      <h1 className="text-3xl font-bold text-primary">Financial RAG Chatbot</h1>
    </main>
  );
}
```

5. **Run Dev Server**
```bash
npm run dev
```

6. **Iteratively Add Components**
- Start with simple HTML structure
- Add state management
- Connect to backend API
- Add styling and animations

---

## 📚 **COMPONENT TEMPLATES**

### **Example: MessageBubble.tsx Template**

```typescript
'use client';

import React from 'react';
import { ChatMessage } from '../types';
import FeedbackButtons from './FeedbackButtons';

interface MessageBubbleProps {
  message: ChatMessage;
  sessionId: string;
}

export default function MessageBubble({ message, sessionId }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}>
      <div className={`max-w-[80%] px-4 py-3 rounded-2xl ${
        isUser
          ? 'bg-primary/20 text-text-primary border border-primary/50'
          : 'bg-background-card text-text-secondary shadow-glass border border-primary/10'
      }`}>
        <p className="text-sm leading-relaxed">{message.content}</p>

        {/* Show feedback buttons only for assistant messages */}
        {!isUser && message.message_id && (
          <FeedbackButtons
            messageId={message.message_id}
            sessionId={sessionId}
            initialScore={message.feedback_score}
          />
        )}

        {/* Timestamp */}
        <p className="text-xs text-text-muted mt-2">
          {new Date(message.created_at || '').toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
```

---

## 🚀 **NEXT STEPS**

1. **Start Backend** (if not running)
```bash
cd backend
python main.py
```

2. **Implement Frontend Components** (follow checklist above)

3. **Test Integration**
- Create session
- Send query
- Submit feedback
- Upload PDF
- Export session

4. **Polish UI**
- Add animations
- Mobile responsive
- Error handling
- Loading states

---

## 💡 **TIPS**

- **Use Existing Patterns:** Follow the structure in `FeedbackButtons.tsx`
- **TailwindCSS:** Use utility classes from `tailwind.config.js`
- **TypeScript:** Import types from `src/types/index.ts`
- **API Calls:** Use `apiClient` from `src/services/api.ts`
- **State:** Use React hooks (`useState`, `useEffect`) or Zustand for global state
- **Testing:** Test each component individually before integration

---

## 📞 **SUPPORT**

If you encounter issues:
1. Check backend is running (`http://localhost:8000/health`)
2. Check browser console for errors
3. Verify API endpoints in backend logs
4. Test API directly using `/docs` (Swagger UI)

---

**🎉 You have all the backend code and frontend scaffolding. Now implement the remaining frontend components using the templates and patterns provided!**
