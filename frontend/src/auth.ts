import NextAuth from "next-auth"
import Credentials from "next-auth/providers/credentials"

export const { handlers, signIn, signOut, auth } = NextAuth({
    providers: [
        Credentials({
            credentials: {
                email: { label: "Email", type: "email" },
                password: { label: "Password", type: "password" },
            },
            authorize: async (credentials) => {
                try {
                    // Logic to request our FastAPI backend
                    const res = await fetch("http://localhost:8000/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            email: credentials.email,
                            password: credentials.password,
                        }),
                    });

                    if (!res.ok) {
                        return null; // Login failed
                    }

                    const tokenData = await res.json();
                    // tokenData contains { access_token, token_type }
                    
                    if (tokenData && tokenData.access_token) {
                        // Fetch user details including name
                        const meRes = await fetch("http://localhost:8000/auth/me", {
                            headers: { "Authorization": `Bearer ${tokenData.access_token}` }
                        });
                        
                        let userName = "User";
                        if (meRes.ok) {
                            const userData = await meRes.json();
                            userName = userData.name || "User";
                        }
                        
                        return { 
                            email: credentials.email as string, 
                            name: userName,
                            accessToken: tokenData.access_token 
                        } as any;
                    }
                    return null;

                } catch (error) {
                    console.error("Auth Error:", error);
                    return null;
                }
            },
        }),
    ],
    callbacks: {
        async jwt({ token, user, account }) {
            if (user) {
                token.accessToken = (user as any).accessToken;
                token.name = (user as any).name;
            }
            return token;
        },
        async session({ session, token }) {
            // Pass the access token and name to the client session
            (session as any).accessToken = token.accessToken;
            if (session.user) {
                session.user.name = token.name as string;
            }
            return session;
        }
    },
    pages: {
        signIn: "/login",
    }
})
