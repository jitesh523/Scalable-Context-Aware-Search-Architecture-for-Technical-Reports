import ChatInterface from "@/components/ChatInterface"

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <header className="border-b sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
        <div className="max-w-4xl mx-auto p-4 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">
            Technical Report Search
          </h1>
          <div className="text-sm text-muted-foreground">
            Powered by RAG & Agents
          </div>
        </div>
      </header>
      <ChatInterface />
    </main>
  )
}
