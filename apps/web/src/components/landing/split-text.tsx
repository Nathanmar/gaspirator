import { cn } from "@/lib/utils";

/** Splits text into masked characters (`[data-char]`) for reveal animations. */
export function SplitChars({
	text,
	className,
}: {
	text: string;
	className?: string;
}) {
	return (
		<span className={className}>
			<span className="sr-only">{text}</span>
			<span aria-hidden="true">
				{Array.from(text).map((char, i) => (
					<span
						// biome-ignore lint/suspicious/noArrayIndexKey: chars repeat and never reorder, position is their identity
						key={i}
						className="-my-[0.12em] inline-block overflow-hidden py-[0.12em] align-bottom"
					>
						<span data-char className="inline-block will-change-transform">
							{char === " " ? " " : char}
						</span>
					</span>
				))}
			</span>
		</span>
	);
}

/** Splits text into words (`[data-word]`); words wrapped in asterisks get the accent style. */
export function SplitWords({
	text,
	accentClassName,
}: {
	text: string;
	accentClassName?: string;
}) {
	const words = text.split(" ");
	return (
		<>
			<span className="sr-only">{text.replaceAll("*", "")}</span>
			<span aria-hidden="true">
				{words.map((word, i) => {
					const accent = word.startsWith("*");
					const clean = word.replaceAll("*", "");
					return (
						// biome-ignore lint/suspicious/noArrayIndexKey: words repeat and never reorder, position is their identity
						<span key={i}>
							<span
								data-word
								className={cn("inline-block", accent && accentClassName)}
							>
								{clean}
							</span>{" "}
						</span>
					);
				})}
			</span>
		</>
	);
}
