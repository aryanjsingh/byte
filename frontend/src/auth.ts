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

                    const user = await res.json();
                    // user contains { access_token, token_type }
                    // We can return an object that NextAuth will store
                    if (user && user.access_token) {
                        return { email: credentials.email as string, accessToken: user.access_token } as any;
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
            }
            return token;
        },
        async session({ session, token }) {
            // Pass the access token to the client session to use in API calls
            (session as any).accessToken = token.accessToken;
            return session;
        }
    },
    pages: {
        signIn: "/login",
    }
})
