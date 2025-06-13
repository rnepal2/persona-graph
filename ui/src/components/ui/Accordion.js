import * as React from "react"

const AccordionContext = React.createContext({
  openItem: null,
  setOpenItem: () => {},
})

function Accordion({ children, variant = "default" }) {
  const [openItem, setOpenItem] = React.useState(null)
  
  const variants = {
    default: "border border-gray-200 rounded-lg divide-y divide-gray-200 bg-white shadow-sm",
    compact: "border border-gray-100 rounded-md divide-y divide-gray-100 bg-white shadow-sm",
    minimal: "divide-y divide-gray-100 bg-white"
  };
  
  return (
    <AccordionContext.Provider value={{ openItem, setOpenItem }}>
      <div className={`${variants[variant]} w-full`}>
        {children}
      </div>
    </AccordionContext.Provider>
  )
}

function AccordionItem({ value, children }) {
  const { openItem, setOpenItem } = React.useContext(AccordionContext)
  const isOpen = openItem === value
  return (
    <div>
      {React.Children.map(children, child =>
        React.cloneElement(child, { isOpen, onToggle: () => setOpenItem(isOpen ? null : value) })
      )}
    </div>
  )
}

function AccordionTrigger({ children, onToggle, isOpen, className = "" }) {
  return (
    <button
      className={`w-full flex justify-between items-center px-4 py-3 font-medium text-left text-gray-900 border-[1px] rounded-md focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-inset hover:bg-gray-50 transition-colors duration-150 ${className}`}
      onClick={onToggle}
      aria-expanded={isOpen}
    >
      {children}
      <span className={`ml-2 transition-transform duration-200 text-gray-500 ${isOpen ? "rotate-180" : "rotate-0"}`}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </span>
    </button>
  )
}

function AccordionContent({ children, isOpen }) {
  return isOpen ? (
    <div className="px-4 py-3 bg-gray-50 text-gray-700 border-t border-gray-200 animate-fade-in">
      {children}
    </div>
  ) : null
}

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }
