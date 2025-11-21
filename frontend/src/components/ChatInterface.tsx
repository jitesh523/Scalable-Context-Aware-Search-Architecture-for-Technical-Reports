"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, FileText, Loader2 } from "lucide-react"
import axios from "axios"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface Message {
    role: "user" | "assistant"
    content: string
    documents?: Array<{ content: string; metadata?: any }>
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: "Hello! I'm your technical research assistant. Ask me anything about your documents.",
        },
    ])
    const [input, setInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || isLoading) return

        const userMessage = input.trim()
        setInput("")
        setMessages((prev) => [...prev, { role: "user", content: userMessage }])
        setIsLoading(true)

        try {
            // Call the backend API
            // Note: In production, use an environment variable for the API URL
            const response = await axios.post("http://localhost:8000/search", {
                query: userMessage,
            })

            const data = response.data

            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: data.answer,
                    documents: data.documents,
                },
            ])
        } catch (error) {
            console.error("Search failed:", error)
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: "Sorry, I encountered an error while processing your request. Please try again.",
                },
            ])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto p-4">
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={cn(
                            "flex w-full",
                            message.role === "user" ? "justify-end" : "justify-start"
                        )}
                    >
                        <div
                            className={cn(
                                "flex max-w-[80%] rounded-lg p-4 gap-3",
                                message.role === "user"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted"
                            )}
                        >
                            <div className="mt-1 shrink-0">
                                {message.role === "user" ? (
                                    <User className="h-5 w-5" />
                                ) : (
                                    <Bot className="h-5 w-5" />
                                )}
                            </div>
                            <div className="flex flex-col gap-2">
                                <div className="whitespace-pre-wrap">{message.content}</div>

                                {/* Citations / Documents */}
                                {message.documents && message.documents.length > 0 && (
                                    <div className="mt-2 pt-2 border-t border-primary-foreground/20">
                                        <p className="text-xs font-semibold mb-2 opacity-70">Sources:</p>
                                        <div className="grid gap-2">
                                            {message.documents.slice(0, 3).map((doc, i) => (
                                                <Card key={i} className="bg-background/10 border-none shadow-none">
                                                    <CardContent className="p-2 text-xs flex items-start gap-2">
                                                        <FileText className="h-3 w-3 mt-0.5 shrink-0" />
                                                        <span className="line-clamp-2 opacity-80">
                                                            {doc.content}
                                                        </span>
                                                    </CardContent>
                                                </Card>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start w-full">
                        <div className="bg-muted rounded-lg p-4 flex items-center gap-2">
                            <Bot className="h-5 w-5" />
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span className="text-sm text-muted-foreground">Thinking...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question about your documents..."
                    className="flex-1"
                    disabled={isLoading}
                />
                <Button type="submit" disabled={isLoading}>
                    <Send className="h-4 w-4 mr-2" />
                    Send
                </Button>
            </form>
        </div>
    )
}
