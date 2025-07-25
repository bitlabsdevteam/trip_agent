import Image from "next/image";
import ClientStreamingWrapper from '@/components/ClientStreamingWrapper';

export default function Home() {
  return (
    <div className="font-sans flex flex-col h-screen w-full">
      <header className="w-full text-center py-4 bg-gray-900 text-white">
        <h1 className="text-3xl font-bold">Trip Agent</h1>
        <p className="text-sm text-gray-300 mt-2">Powered by Next.js and Flask</p>
      </header>
      
      <main className="flex-1 w-full bg-white dark:bg-gray-800 overflow-hidden">
        <ClientStreamingWrapper />
      </main>
      <footer className="w-full py-4 bg-gray-100 dark:bg-gray-900 flex gap-[24px] flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/file.svg"
            alt="File icon"
            width={16}
            height={16}
          />
          Learn
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/window.svg"
            alt="Window icon"
            width={16}
            height={16}
          />
          Examples
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/globe.svg"
            alt="Globe icon"
            width={16}
            height={16}
          />
          Go to nextjs.org →
        </a>
      </footer>
    </div>
  );
}
