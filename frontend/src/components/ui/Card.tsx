import { ReactNode, MouseEventHandler } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
  onClick?: MouseEventHandler<HTMLDivElement>;
  hoverable?: boolean;
};

export function Card({ children, className = "", onClick, hoverable }: CardProps) {
  const base = "bg-white rounded-xl border border-gray-200/70 shadow-sm";
  const interactive = onClick || hoverable
    ? "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
    : "";
  return (
    <div className={`${base} ${interactive} ${className}`} onClick={onClick}>
      {children}
    </div>
  );
}

Card.Header = function CardHeader({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`px-6 pt-6 pb-3 ${className}`}>{children}</div>;
};

Card.Body = function CardBody({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`px-6 pb-6 ${className}`}>{children}</div>;
};
