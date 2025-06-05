import * as React from "react"

const AccordionContext = React.createContext({
  openItem: null,
  setOpenItem: () => {},
})

function Accordion({ children }) {
  const [openItem, setOpenItem] = React.useState(null)
  return (
    <AccordionContext.Provider value={{ openItem, setOpenItem }}>
      <div className="border rounded-md divide-y w-full bg-white shadow">
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

function AccordionTrigger({ children, onToggle, isOpen }) {
  return (
    <button
      className="w-full flex justify-between items-center p-4 font-medium text-left focus:outline-none hover:bg-gray-50 transition"
      onClick={onToggle}
      aria-expanded={isOpen}
    >
      {children}
      <span className={`ml-2 transition-transform ${isOpen ? "rotate-180" : "rotate-0"}`}>▼</span>
    </button>
  )
}

function AccordionContent({ children, isOpen }) {
  return isOpen ? (
    <div className="p-4 border-t bg-gray-50 text-gray-700 animate-fade-in">
      {children}
    </div>
  ) : null
}

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }
